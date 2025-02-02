import torch
from torch import nn
from torch.autograd import Variable

class Siamese(nn.Module):
  def __init__(self, config):
    super().__init__()
    self.lstm = LSTM(config)

    self.input_dim = 4 * self.lstm.direction * self.lstm.hidden_size
    self.mode = config['model']['embed_mode']
    self.loss_mode = config['model']['loss_mode']

    layers = [
      nn.Linear(self.input_dim, int(self.input_dim / 2)),
      nn.Linear(int(self.input_dim / 2), 3)]
    if self.loss_mode == 'mse':
      layers = [
        nn.Linear(self.input_dim, int(self.input_dim / 2)),
        nn.Linear(int(self.input_dim / 2), 1)]
    self.classifier = nn.Sequential(*layers)

  def forward(self, sentence1, sentence2):
    hidden_number1, memory_cell1 = self.lstm.initHidden()
    hidden_number2, memory_cell2 = self.lstm.initHidden()

    if self.mode == 'word':
      for word1 in sentence1.split():
        vector1, hidden_number1, memory_cell1 = self.lstm(word1, hidden_number1, memory_cell1)

      for word2 in sentence2.split():
        vector2, hidden_number2, memory_cell2 = self.lstm(word2, hidden_number2, memory_cell2)

    elif self.mode == 'char':
      for i in range(len(sentence1)):
        vector1, hidden_number1, memory_cell1 = self.lstm(sentence1[i], hidden_number1, memory_cell1)

      for j in range (len(sentence2)):
        vector1, hidden_number1, memory_cell1 = self.lstm(sentence2[j], hidden_number1, memory_cell1)

    features = torch.cat((vector1, vector2, torch.abs(vector1 - vector2), vector1 * vector2), 2)
    output = self.classifier(features)
    return output

class LSTM(nn.Module):
  def __init__(self, config):
    super().__init__()
    self.embed_size = config['model']['embed_size']
    self.batch_size = config['model']['batch_size']
    self.hidden_size = config['model']['encoder']['hidden_size']
    self.num_layers = config['model']['encoder']['num_layers']
    self.bidir = config['model']['encoder']['bidirectional']
    self.dropout = config['model']['encoder']['dropout']
    self.lstm = nn.LSTM(input_size=self.embed_size, hidden_size=self.hidden_size, dropout=self.dropout, num_layers=self.num_layers, bidirectional=self.bidir)

    self.direction = 2 if self.bidir else 1
    self.embeds = config['embedding']
    self.vocab = config['vocab']
  
  def initHidden(self):
    hidden_number = Variable(torch.randn(self.direction * self.num_layers, self.batch_size, self.hidden_size))
    memory_cell =  Variable(torch.randn(self.direction * self.num_layers, self.batch_size, self.hidden_size))
    return hidden_number, memory_cell

  def forward(self, input, hidden, cell):
    input_index = self.vocab[input]
    input = self.embeds(torch.tensor(input_index)).view(1, 1, -1)
    output, (hidden, cell) = self.lstm(input, (hidden, cell))
    return output, hidden, cell