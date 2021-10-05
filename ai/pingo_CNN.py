import matplotlib.pylab as plt
import tensorflow as tf
import os
import numpy as np
import PIL.Image as Image

# 시간측정
import time
import datetime

# 시간측정끝
from tensorflow.python.client import device_lib
from tensorflow.python.ops.gen_array_ops import reshape

# print(device_lib.list_local_devices())


os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# print(tf.__version__)

start = time.time()  # 시작 시간 저장

data_dir = "./datasets/pingo"
IMG_SIZE = (300, 300)
BATCH_SIZE = 256
initial_epochs = 10000


# image_dataset_from_directory를 이용해서 해당 폴더에서 이미지 가져오기
train_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="training",
    seed=456,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    color_mode="rgb",
    # color_mode="grayscale",
    # label_mode="categorical",
)

validation_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="validation",
    seed=456,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    color_mode="rgb",
    # color_mode="grayscale",
    # label_mode="categorical",
)

# 클래스 이름 가져오기
class_names = train_dataset.class_names

# 이미지 shape 알아보기위해
for image_batch, labels_batch in train_dataset:
    print(image_batch.shape)
    print(labels_batch.shape)
    break

# 캐싱, 셔플, 프리페치
AUTOTUNE = tf.data.experimental.AUTOTUNE
train_dataset = train_dataset.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
validation_dataset = validation_dataset.cache().prefetch(buffer_size=AUTOTUNE)


# plt.figure(figsize=(10, 10))
# for images, labels in train_dataset.take(1):
#     for i in range(9):
#         ax = plt.subplot(3, 3, i + 1)
#         plt.imshow(images[i].numpy().astype("uint8"))
#         plt.title(class_names[labels[i]])
#         plt.axis("off")

# plt.figure(figsize=(10, 10))
# for images, labels in train_dataset.take(3):
#     for i in range(9):
#         ax = plt.subplot(3, 3, i + 1)
#         plt.imshow(images[i].numpy().astype("uint8"))
#         plt.title(class_names[labels[i]])
#         plt.axis("off")

# plt.show()

# 전처리 -> 픽셀값 조정
rescale = tf.keras.Sequential(
    [tf.keras.layers.experimental.preprocessing.Rescaling(1.0 / 255)]
)
# 전처리 -> 데이터 증강
data_augmentation = tf.keras.Sequential(
    [
        tf.keras.layers.experimental.preprocessing.RandomFlip("horizontal"),
        tf.keras.layers.experimental.preprocessing.RandomRotation(0.2),
    ]
)


for image, _ in train_dataset.take(1):
    plt.figure(figsize=(10, 10))
    first_image = image[0]
    for i in range(9):
        ax = plt.subplot(3, 3, i + 1)
        augmented_image = data_augmentation(tf.expand_dims(first_image, 0))
        plt.imshow(augmented_image[0] / 255)
        plt.axis("off")
# plt.show()


# 모델 정의
model = tf.keras.models.Sequential(
    [
        rescale,
        data_augmentation,
        tf.keras.layers.Conv2D(
            16, (3, 3), activation="relu", input_shape=(300, 300, 3)
        ),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(32, (3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(64, (3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(128, (3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Conv2D(256, (3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(1024, activation="relu"),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(10, activation="softmax"),
    ]
)


# 모델 컴파일
model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
    # optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
)

print(class_names)
print("-----------------------------------------")
print(train_dataset)
print("-----------------------------------------")


# 학습 시작
history = model.fit(
    train_dataset, validation_data=validation_dataset, epochs=initial_epochs
)

score = model.evaluate(validation_dataset)

# 모델 요약 출력
model.summary()


print("loss=", score[0])  # loss
print("accuracy=", score[1])  # acc

save_accuracy = str(round(score[1], 3))
save_loss = str(round(score[0], 3))
save_BATCH_SIZE = str(BATCH_SIZE)
save_initial_epochs = str(initial_epochs)

# print(accuracy) #정확도
# print(loss)     #로스

model.save(
    "./models/pingo_"
    + save_BATCH_SIZE
    + "_"
    + save_initial_epochs
    + "_"
    + save_accuracy
    + "_"
    + save_loss
    + ".h5"
)
# model.save("./models/pingo.h5")

predictions = model.predict(validation_dataset)


score = tf.nn.softmax(predictions[0])
print(
    "This image most likely belongs to {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)


test_path = "./datasets/pingo/banana_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 banana 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/bulb_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 bulb 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/calculator_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 calculator 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/carrot_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 carrot 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/clock_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 clock 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/crescent_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 crescent 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/diamond_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 diamond 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/icecream_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 icecream 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)
test_path = "./datasets/pingo/strawberry_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(
    "원본은 strawberry 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)


# np.set_printoptions(precision=3)

test_path = "./datasets/pingo/t-shirt_test.png"
img = tf.keras.preprocessing.image.load_img(
    test_path, target_size=IMG_SIZE, color_mode="rgb"
)

img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

print(predictions)


print(
    "원본은 t-shirt 추측은 {} with a {:.2f} percent confidence.".format(
        class_names[np.argmax(predictions[0])], 100 * np.max(predictions[0])
    )
)

end = time.time()
sec = end - start
result = datetime.timedelta(seconds=sec)
print(result)
result_list = str(datetime.timedelta(seconds=sec)).split(".")
print(result_list[0])

acc = history.history["accuracy"]
val_acc = history.history["val_accuracy"]

loss = history.history["loss"]
val_loss = history.history["val_loss"]

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(acc, label="Training Accuracy")
plt.plot(val_acc, label="Validation Accuracy")
plt.legend(loc="lower right")
plt.ylabel("Accuracy")
plt.ylim([min(plt.ylim()), 1])
plt.title("Training and Validation Accuracy")

plt.subplot(2, 1, 2)
plt.plot(loss, label="Training Loss")
plt.plot(val_loss, label="Validation Loss")
plt.legend(loc="upper right")
plt.ylabel("Cross Entropy")
plt.ylim([0, 1.0])
plt.title("Training and Validation Loss")
plt.xlabel("epoch")


plt.show()
plt.savefig(
    "./models/pingo_"
    + save_BATCH_SIZE
    + "_"
    + save_initial_epochs
    + "_"
    + save_accuracy
    + "_"
    + save_loss
    + ".png"
)
