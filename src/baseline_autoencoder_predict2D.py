from keras.layers import Conv2D
from keras.layers import UpSampling2D
from keras.layers import Input
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Reshape
from keras.models import Model
from keras.models import model_from_json

from keras.preprocessing.image import img_to_array, load_img
from sklearn.model_selection import train_test_split
from skimage import io, color
from os import listdir
import numpy as np

dim = 256

# encoder
inputs = Input(shape=(dim, dim, 1,))
encoder_output = Conv2D(64, (3, 3), activation='relu', padding='same', strides=2)(inputs)
encoder_output = Conv2D(128, (3, 3), activation='relu', padding='same')(encoder_output)
encoder_output = Conv2D(128, (3, 3), activation='relu', padding='same', strides=2)(encoder_output)
encoder_output = Conv2D(256, (3, 3), activation='relu', padding='same')(encoder_output)
encoder_output = Conv2D(256, (3, 3), activation='relu', padding='same', strides=2)(encoder_output)
encoder_output = Conv2D(512, (3, 3), activation='relu', padding='same')(encoder_output)
encoder_output = Conv2D(512, (3, 3), activation='relu', padding='same')(encoder_output)
encoder_output = Conv2D(256, (3, 3), activation='relu', padding='same')(encoder_output)

# decoder
decoder_output = Conv2D(128, (3, 3), activation='relu', padding='same')(encoder_output)
decoder_output = UpSampling2D((2, 2))(decoder_output)
decoder_output = Conv2D(64, (3, 3), activation='relu', padding='same')(decoder_output)
decoder_output = UpSampling2D((2, 2))(decoder_output)
decoder_output = Conv2D(32, (3, 3), activation='relu', padding='same')(decoder_output)
decoder_output = Conv2D(16, (3, 3), activation='relu', padding='same')(decoder_output)
decoder_output = Conv2D(2, (3, 3), activation='tanh', padding='same')(decoder_output)
decoder_output = UpSampling2D((2, 2))(decoder_output)

# complete model
model = Model(inputs=inputs, outputs=decoder_output)
model.compile(loss='mse', optimizer='adam', metrics=['acc'])
print(model.summary())


cartoon_dir = '../img/original/test_cartoon/'

Col = []
BW = []
i = 0
for filename in listdir(cartoon_dir):
    i += 1
    print(i)
    data_orig = img_to_array(load_img(cartoon_dir + filename, target_size=(dim, dim)))
    data_orig = 1.0 / 255 * data_orig
    data_orig_lab = color.rgb2lab(data_orig)

    data_orig_ab = data_orig_lab[:, :, 1:3]
    data_orig_l = data_orig_lab[:, :, 0]
    data_orig_l = data_orig_lab[:, :, 0]  / 100  # PROVA A RUNNARE SENZA QUESTA NORMALIZZAZIONE SE I RISULTATI FANNO CACARE

    Col.append(data_orig_ab)
    BW.append(data_orig_l)

Col = np.array(Col)
BW = np.array(BW)


train_Col, _, train_BW, _ = train_test_split(Col, BW, test_size=0.3, random_state=42)
print()

epochs = 50
fit_history = model.fit(train_BW, train_Col, epochs=epochs, verbose=1)
print()

model_json = model.to_json()
with open('model_2D_'+str(epochs)+'.json', "w") as json_file:
    json_file.write(model_json)
# serialize weights to HDF5
model.save_weights('model_2D_'+str(epochs)+'.h5')
print("Saved model to disk")
print()


epochs = 50
# load json and create model
json_file = open('model_2D_'+str(epochs)+'.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
loaded_model = model_from_json(loaded_model_json)
# load weights into new model
loaded_model.load_weights('model_2D_'+str(epochs)+'.h5')
print("Loaded model from disk")
print()


AB = []
i = 0
for img in BW:
    i += 1
    print(i)
    img = np.reshape(img, (1, dim, dim, 1))
    cartoon_ab = loaded_model.predict(img)
    cartoon_ab = np.reshape(cartoon_ab, (dim, dim, 2))
    AB.append(cartoon_ab)


original_dir = '../img/original/test/'

L = []
i = 0
for filename in listdir(cartoon_dir):
    i += 1
    print(i)
    data_rgb = img_to_array(load_img(original_dir + filename, target_size=(dim, dim)))
    data_rgb = 1.0 / 255 * data_rgb
    data_lab = color.rgb2lab(data_rgb)
    l = data_lab[:, :, 0]
    L.append(l)


results_dir = '../img/colorized/baseline/baseline2D/epochs_'+str(epochs)+'/'

results = np.empty((dim, dim, 3))
img = 0
i = 0
for filename in listdir(cartoon_dir):
    i += 1
    print(i)
    results[:, :, 0] = L[img]    # values should be in (0,100)
    results[:, :, 1:3] = AB[img] # values should be in (-100,100)
    results = color.lab2rgb(results)
    io.imsave(results_dir + filename, results)
    img += 1
