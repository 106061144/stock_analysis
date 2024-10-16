import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import plotly.express as px
import yfinance as yf
import os
import tqdm
import time


def create_dataset(dataset, lookback):
    X, y = [], []
    for i in range(len(dataset)-lookback):
        feature = dataset[i:i+lookback, :]
        diff_ratio = (dataset[i+lookback][-2]-dataset[i +
                      lookback-1][-2])/dataset[i+lookback-1][-2]
        if diff_ratio >= 0.3:
            target = 0
        elif (diff_ratio < 0.3) and (diff_ratio >= 0):
            target = 1
        elif (diff_ratio > -0.3) and (diff_ratio < 0):
            target = 2
        else:
            target = 3
        X.append(feature)
        y.append(np.int64(target))
    return torch.tensor(X), torch.tensor(y)


root_folder = "DataBase"
all_files = os.listdir(root_folder)
start_time = time.time()
for i, file in enumerate(all_files[:10]):
    df = pd.read_csv(root_folder+'/'+file, index_col=0)
    timeseries = df[["Open", "High", "Low", "Close", "Volume"]
                    ].values.astype('float32')
    # normalization
    scaler = StandardScaler()
    timeseries = scaler.fit_transform(timeseries)
    # train-val split for time series
    train_size = int(len(timeseries) * 0.67)
    test_size = len(timeseries) - train_size
    train, val = timeseries[:train_size], timeseries[train_size:]

    lookback = 30
    X_train1, y_train1 = create_dataset(train, lookback=lookback)
    X_val1, y_val1 = create_dataset(val, lookback=lookback)
    if i == 0:
        X_train = X_train1
        y_train = y_train1
        X_val = X_val1
        y_val = y_val1
    else:
        X_train = torch.cat((X_train, X_train1), dim=0)
        y_train = torch.cat((y_train, y_train1), dim=0)
        X_val = torch.cat((X_val, X_val1), dim=0)
        y_val = torch.cat((y_val, y_val1), dim=0)
print(f'The data extraction takes {time.time()-start_time} seconds')


class LSTM_Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=5, hidden_size=64,
                            num_layers=2, batch_first=True)
        self.linear = nn.Linear(64, 4)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        x, _ = self.lstm(x)
        x = self.dropout(x)
        x = x[:, -1, :]
        x = self.linear(x)
        return x


model = LSTM_Model()
model = model.to('cuda' if torch.cuda.is_available() else 'cpu')
# optimizer = optim.Adam(model.parameters())
# 使用SDG或Adam演算法的lstm經常會用RMSprop做為優化方向，因為，它收斂的速度會比較快，原因是RMSprop 的學習速率(learning rate)會隨著之前的梯度總和作反向的調整。
optimizer = optim.RMSprop(model.parameters())
loss_func = nn.CrossEntropyLoss()
num_epochs = 1000
batch_size = 8
train_loader = data.DataLoader(data.TensorDataset(
    X_train, y_train), shuffle=False, batch_size=batch_size)
test_loader = data.DataLoader(data.TensorDataset(
    X_val, y_val), shuffle=False, batch_size=batch_size)


def fit_model(model, loss_func, optimizer, num_epochs, train_loader, test_loader):
    # Traning the Model
    # history-like list for store loss & acc value
    training_loss = []
    training_accuracy = []
    validation_loss = []
    validation_accuracy = []
    for epoch in range(num_epochs):
        # training model & store loss & acc / epoch
        model.train()
        for i, (feature, labels) in enumerate(train_loader):
            outputs = model(feature)
            train_loss = loss_func(outputs, labels)
            # Clear gradients
            optimizer.zero_grad()
            # Calculate gradients
            train_loss.backward()
            # Update parameters
            optimizer.step()

        # evaluate model & store loss & acc / epoch
        correct_train = 0
        total_train = 0
        correct_test = 0
        total_test = 0
        model.eval()
        with torch.no_grad():
            outputs = model(X_train)
            train_loss = loss_func(outputs, y_train)
            predicted = torch.max(outputs.data, 1)[1]
            if epoch % 100 == 0:
                print(predicted[:10])
            correct_train = (predicted == y_train).float().sum()
            outputs = model(X_val)
            val_loss = loss_func(outputs, y_val)
            predicted = torch.max(outputs.data, 1)[1]
            correct_val = (predicted == y_val).float().sum()

            train_accuracy = 100 * correct_train / float(len(y_train))
            training_accuracy.append(train_accuracy)
            training_loss.append(train_loss.data)
            val_accuracy = 100 * correct_val / float(len(y_val))
            validation_accuracy.append(val_accuracy)
            validation_loss.append(val_loss.data)
        if epoch % 100 == 0:
            print('Train Epoch: {}/{} Traing_Loss: {} Traing_acc: {:.6f}% Val_Loss: {} Val_accuracy: {:.6f}%'.format(
                epoch+1, num_epochs, train_loss.data, train_accuracy, val_loss.data, val_accuracy))
    return training_loss, training_accuracy, validation_loss, validation_accuracy


training_loss, training_accuracy, validation_loss, validation_accuracy = fit_model(
    model, loss_func, optimizer, num_epochs, train_loader, test_loader)
