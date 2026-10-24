"""
SortSense - custom waste classifier training (MobileNetV2 transfer learning)

Dataset layout (e.g. TrashNet / TACO crops + our own campus photos):
    data/
      biodegradable/  *.jpg
      recyclable/     *.jpg
      non_recyclable/ *.jpg
      hazardous/      *.jpg

Run:
    pip install tensorflow==2.15 scikit-learn
    python train_sortsense.py --data data --epochs 15
Outputs:
    sortsense.keras, sortsense.tflite (int8, for ESP32/phone), metrics.txt (accuracy + confusion matrix)
"""
import argparse, numpy as np, tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

p = argparse.ArgumentParser()
p.add_argument("--data", default="data"); p.add_argument("--epochs", type=int, default=15)
p.add_argument("--img", type=int, default=224); p.add_argument("--threshold", type=float, default=0.80)
a = p.parse_args()

kw = dict(validation_split=0.2, seed=42, image_size=(a.img, a.img), batch_size=32)
train = tf.keras.utils.image_dataset_from_directory(a.data, subset="training", **kw)
val = tf.keras.utils.image_dataset_from_directory(a.data, subset="validation", shuffle=False, **kw)
classes = train.class_names
AUT = tf.data.AUTOTUNE; train, val = train.prefetch(AUT), val.prefetch(AUT)

aug = tf.keras.Sequential([tf.keras.layers.RandomFlip("horizontal"), tf.keras.layers.RandomRotation(0.15),
                           tf.keras.layers.RandomZoom(0.2), tf.keras.layers.RandomContrast(0.3),
                           tf.keras.layers.RandomBrightness(0.3)])  # simulates bad bin lighting
base = tf.keras.applications.MobileNetV2(input_shape=(a.img, a.img, 3), include_top=False, weights="imagenet")
base.trainable = False
inp = tf.keras.Input((a.img, a.img, 3))
x = tf.keras.applications.mobilenet_v2.preprocess_input(aug(inp))
x = tf.keras.layers.GlobalAveragePooling2D()(base(x, training=False))
x = tf.keras.layers.Dropout(0.3)(x)
out = tf.keras.layers.Dense(len(classes), activation="softmax")(x)
model = tf.keras.Model(inp, out)

model.compile(tf.keras.optimizers.Adam(1e-3), "sparse_categorical_crossentropy", ["accuracy"])
model.fit(train, validation_data=val, epochs=a.epochs // 2)
base.trainable = True                       # fine-tune top layers
for l in base.layers[:-40]: l.trainable = False
model.compile(tf.keras.optimizers.Adam(1e-5), "sparse_categorical_crossentropy", ["accuracy"])
model.fit(train, validation_data=val, epochs=a.epochs - a.epochs // 2,
          callbacks=[tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)])

# --- evaluation incl. confidence-threshold behaviour ---
y_true = np.concatenate([y.numpy() for _, y in val]); prob = model.predict(val)
y_pred, conf = prob.argmax(1), prob.max(1); auto = conf >= a.threshold
rep = classification_report(y_true, y_pred, target_names=classes)
lines = [rep, "Confusion matrix:\n" + str(confusion_matrix(y_true, y_pred)),
         f"Overall accuracy: {(y_true == y_pred).mean():.3f}",
         f"Auto-sorted share (conf >= {a.threshold}): {auto.mean():.3f}",
         f"Accuracy on auto-sorted items: {(y_true[auto] == y_pred[auto]).mean():.3f}",
         f"Items sent to human confirm: {(~auto).sum()}"]
open("metrics.txt", "w").write("\n\n".join(lines)); print("\n\n".join(lines))

model.save("sortsense.keras")
def rep_data():
    for x, _ in train.take(50): yield [tf.cast(x, tf.float32)]
conv = tf.lite.TFLiteConverter.from_keras_model(model)
conv.optimizations = [tf.lite.Optimize.DEFAULT]; conv.representative_dataset = rep_data
open("sortsense.tflite", "wb").write(conv.convert())
open("labels.txt", "w").write("\n".join(classes)); print("Saved sortsense.tflite, labels:", classes)
