import numpy as np
from PIL import Image
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import torch.nn as nn
import torchvision

from utils_alexnet import *

def get_labels(labels, num):
    final_labels = None
    for label in labels:
        if final_labels is None:
            final_labels = np.full(num, label)
        else:
            final_labels = np.concatenate((final_labels, np.full(num, label)), axis=0)
    return final_labels


lab = ["cassette player", "chain saw", "church", "gas pump", "golf ball", "French horn", "parachute",
          "Rhodesian ridgeback", "Samoyed", "English springer", "tench", "garbage truck"]
labels = [482, 491, 497, 571, 574, 566, 701, 159, 258, 217, 0, 569]
# labels_LOO = [482, 491, 497, 571, 574, 566, 701, 159, 258, 217, 0]

train_labels = get_labels(labels, 150)
# train_labels = get_labels(labels_LOO, 150)
test_labels = get_labels(labels, 50)

# Load scaled data
data_train_scaled = np.load('../resources/data_train_scaled.npy')
# data_train_scaled = np.load('../resources/data_train_scaled_LOO.npy')
data_test_scaled = np.load('../resources/data_test_scaled.npy')

# AlexNet requires images to be with shape: 3x256x256
data_train_scaled = data_train_scaled.transpose((0, 3, 1, 2))
data_test_scaled = data_test_scaled.transpose((0, 3, 1, 2))

train_dataset = MyDataset(list(data_train_scaled), train_labels)
test_dataset = MyDataset(list(data_test_scaled), test_labels)

# Validation set:
train_percentage = 0.8
num_train_examples = int(len(train_dataset) * train_percentage)
num_valid_examples = len(train_dataset) - num_train_examples
train_dataset, valid_dataset = torch.utils.data.random_split(train_dataset, [num_train_examples, num_valid_examples])

# Create iterators:
BATCH_SIZE = 32
train_iterator = DataLoader(train_dataset, shuffle=True, batch_size=BATCH_SIZE)
valid_iterator = DataLoader(valid_dataset, batch_size=BATCH_SIZE)
test_iterator = DataLoader(test_dataset, batch_size=BATCH_SIZE)

#for (x,y) in train_iterator:
#    print(x.shape) # torch.Size([64, 3, 256, 256])
#    print(y.shape) # torch.Size([64])

# Pre-trained model:
alexnet = torchvision.models.alexnet(pretrained=True)
# print(alexnet.classifier[-1]) # Linear(in_features=4096, out_features=1000, bias=True)
alexnet.double()

# Freeze all layers except last Fully Connected layer:
for parameter in alexnet.features.parameters():
    parameter.requires_grad = False
for parameter in alexnet.classifier[:-1].parameters():
    parameter.requires_grad = False

# Feature extraction:
device = torch.device('cpu')
criterion = nn.CrossEntropyLoss()
criterion = criterion.to(device)
optimizer = optim.Adam(alexnet.parameters(), lr=1e-4)
alexnet = alexnet.to(device)

# Train the last FC layer:
N_EPOCHS = 3
train_losses, train_acc, valid_losses, valid_acc = model_training(N_EPOCHS, alexnet, train_iterator,
                                                                  valid_iterator, optimizer, criterion,
                                                                  device, 'alexnet_feat_extract.pt')

model_testing(alexnet, test_iterator, criterion, device, 'alexnet_feat_extract.pt')

test_loss_BW, test_acc_BW = evaluate(alexnet, test_iterator, criterion, device)

# Save results to files
with open('../resources/classification/Test_Results_BW.txt', 'w') as f:
    f.write("Test loss:" + str(test_loss_BW) + '\n')
    f.write("Test acc:" + str(test_acc_BW) + '\n')

with open('../resources/classification/Train_Results_BW.txt', 'w') as f:
    f.write("Train loss:\n")
    f.writelines('\n'.join([str(i) for i in train_losses]))
    f.write("\nTrain acc:\n")
    f.writelines('\n'.join([str(i) for i in train_acc]))

with open('../resources/classification/Valid_Results_BW.txt', 'w') as f:
    f.write("Valid loss:\n")
    f.writelines('\n'.join([str(i) for i in valid_losses]))
    f.write("\nValid acc:\n")
    f.writelines('\n'.join([str(i) for i in valid_acc]))