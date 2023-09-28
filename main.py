# -*- coding: utf-8 -*-
"""Untitled12.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1OObTT_iaEFzsL5dFT4hlJusqN6hMhuAm
"""

import torch
with open('input.txt') as fp:
    shakespeare_text = fp.read()

from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

tokenizer = Tokenizer(BPE(unk_token = "[UNK]"))
trainer = BpeTrainer(special_tokens = ["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])

tokenizer.pre_tokenizer = Whitespace()

files = ['input.txt']
tokenizer.train(files, trainer)

tokenizer.save('char_rnn_tokenizer')

from transformers import PreTrainedTokenizerFast

fast_tokenizer = PreTrainedTokenizerFast(tokenizer_object = tokenizer)

max_id = fast_tokenizer.vocab_size

encoded = fast_tokenizer.encode(shakespeare_text, add_special_tokens=False)

train_size = len(encoded) * 90 // 100
train_encoded = encoded[:train_size]

sequences = []
for n in range(0,len(train_encoded)):
    full_length = train_encoded[n: n+ 101]
    if len(full_length) == 101:
        sequences.append(full_length)

tensors = [torch.LongTensor(i) for i in sequences]

from torch.utils.data import Dataset

inputs = []
targets = []
for i in range(len(tensors)):
    try:
        targets.append(tensors[i+1])
        inputs.append(tensors[i])
    except:
        break

class MyData(Dataset):
    def __init__(self):
        self.inputs = []
        self.targets = []
        for i in range(len(tensors)):
            try:
                self.targets.append(tensors[i+1])
                self.inputs.append(tensors[i])
            except:
                break
    def __len__(self):
        return len(self.inputs)
    def __getitem__(self, index):
        inputs = self.inputs[index]
        targets = self.targets[index]
        return inputs, targets

from torch.utils.data import DataLoader

data = MyData()

loader = DataLoader(data, batch_size=256, shuffle=True)

from torch.nn import Sequential
from torch import nn
from torch import optim

class CharRNN(nn.Module):
    def __init__(self):
        super(CharRNN, self).__init__()
        self.embedding = nn.Embedding(num_embeddings=max_id, embedding_dim=768)
        self.gru_1 = nn.GRU(768,256, batch_first = True, dropout = 0.2)
        self.gru_2 = nn.GRU(256,256, batch_first = True, dropout = 0.2, bidirectional = True)
        self.linear = nn.Linear(256 * 2, max_id)
    def forward(self, x):
        x = self.embedding(x)
        gru_out, hidden = self.gru_1(x)
        x, hidden_2 = self.gru_2(gru_out)
        out = self.linear(x)
        return out

model = CharRNN()

optimizer = optim.Adam(model.parameters(), lr = 0.001)
loss_fn = torch.nn.CrossEntropyLoss()

epochs = 20
from tqdm import tqdm
device  = torch.device('cuda')
model.to(device)
for epoch in tqdm(range(epochs), total = epochs):
    training_loss = 0.0
    valid_loss = 0.0
    model.train()
    for batch in loader:
        optimizer.zero_grad()
        inputs, targets = batch
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = model(inputs)
        outputs_flat = outputs.view(-1,max_id)
        targets_flat = targets.view(-1)
        loss = loss_fn(outputs_flat, targets_flat)
        loss.backward()
        optimizer.step()
        training_loss += loss.data.item()
    training_loss /= len(loader)
    print(f'After {epoch} epochs loss is {training_loss}')

