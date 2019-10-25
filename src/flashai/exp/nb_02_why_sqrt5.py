
##########################################
###### This file was autogenerated. ######
######### DO NOT EDIT this file. #########
##########################################
### file to edit: dev_nb/imflash217__02_why_sqrt5.ipynb ####

from exp.nb_02_full_connected import *

def get_data(url=MNIST_URL):
    path = datasets.download_data(url=url, ext=".gz")
    with gzip.open(path, "rb") as f:
        ((x_train, y_train), (x_valid, y_valid), _) = pickle.load(f, encoding="latin-1")
    return map(torch.tensor, (x_train, y_train, x_valid, y_valid))

def normalize(inp, mean, std):
    return (inp-mean)/std

def stats(inp):
    return inp.mean(), inp.std()