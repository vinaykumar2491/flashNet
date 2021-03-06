
##########################################
###### This file was autogenerated. ######
######### DO NOT EDIT this file. #########
##########################################
### file to edit: dev_nb/imflash217__03_cuda_cnn_hooks_init.ipynb ####


from exp.nb_03_early_stopping import *
torch.set_num_threads(2)


def normalize_to(train, valid):
    mean = train.mean()
    std  = train.std()
    return normalize(train, mean, std), normalize(valid, mean, std)


class Lambda(torch.nn.Module):
    def __init__(self, func):
        super().__init__()
        self.func = func
    def forward(self, x):
        return self.func(x)

def flatten(x):
    return x.view(x.shape[0], -1)

def mnist_resize(x):
    return x.view(-1, 1, 28, 28)


class CudaCallback(Callback):
    def begin_fit(self):
        self.model.cuda()
    def begin_batch(self):
        self.run.xb = self.xb.cuda()
        self.run.yb = self.yb.cuda()


class BatchTransformXCallback(Callback):
    _order = 2
    def __init__(self, tfm):
        self.tfm = tfm
    def begin_batch(self):
        self.run.xb = self.tfm(self.xb)

def view_tfm(*size):
    def _inner(x):
        return x.view(*((-1,) + size))
    return _inner


def get_runner(model, data, lr=0.6, cbs=None, opt_func=None, loss_func=F.cross_entropy):
    if opt_func is None:
        opt_func = optim.SGD
    opt = opt_func(model.parameters(), lr=lr)
    learner = Learner(model, opt, loss_func, data)
    run = Runner(cb_funcs=listify(cbs))
    return learner, run


def children(module):
    return list(module.children())

class Hook():
    def __init__(self, module, func):
        self.hook = module.register_forward_hook(partial(func, self))
    def remove(self):
        self.hook.remove()
    def __del__(self):
        self.remove()

def append_stats(hook, module, inp, out):
    if not hasattr(hook, "stats"):
        hook.stats = ([], [])
    means, stds = hook.stats
    means.append(out.data.mean())
    stds.append(out.data.std())



class ListContainer():
    def __init__(self, items):
        self.items = listify(items)
    def __len__(self):
        return len(self.items)
    def __getitem__(self, idx):
        if isinstance(idx, (int, slice)):                         ### int or slice indexing
            return self.items[idx]
        if isinstance(idx[0], bool):                              ### boolean mask indexing
            assert len(idx) == len(self)                          ### checking if "idx" is a boolean mask of same length
            return [x for msk, x in zip(idx, self.items) if msk]
        return [self.items[i] for i in idx]                       ### list of indices indexing
    def __iter__(self):
        return iter(self.items)
    def __setitem__(self, idx, x):
        self.items[idx] = x
    def __delitem__(self, idx):
        del(self.items[idx])
    def __repr__(self):
        result = f"{self.__class__.__name__}({len(self)} items)\n{self.items[:10]}"
        if len(self)>10:
            result = result[:-1] + ", ...]"
        return result



from torch.nn import init

class Hooks(ListContainer):
    def __init__(self, modules, func):
        super().__init__([Hook(m, func) for m in modules])         ### initializing the parent ListContainer
    def __enter__(self, *args):
        return self
    def __exit__(self, *args):
        return self.remove()                                       ### removing the hook on exit
    def __del__(self):
        self.remove()                                              ### removing the hook on delete

    def __delitem__(self, idx):
        self[idx].remove()                                         ### removingg the particular hook
        super().__delitem__(idx)                                   ### deleting the parent ListContainer item

    def remove(self):
        for hook in self:
            hook.remove()



def get_cnn_layers(data, nfs, layer, **kwargs):
    nfs = [1] + nfs
    return [layer(nfs[i], nfs[i+1], 5 if i==0 else 3, **kwargs)
            for i in range(len(nfs)-1)] + [
            torch.nn.AdaptiveAvgPool2d(1),
            Lambda(flatten),
            torch.nn.Linear(nfs[-1], data.c)]

def conv_layer(ni, nf, ks=3, stride=2, **kwargs):
    return torch.nn.Sequential(
            torch.nn.Conv2d(ni, nf, ks, stride=stride, padding=ks//2),
            GeneralReLU(**kwargs))

class GeneralReLU(torch.nn.Module):
    def __init__(self, leak=None, sub=None, maxv=None):
        super().__init__()
        self.leak = leak                                  ### amount of negative-slope in the ReLU
        self.sub  = sub                                   ### amount to subtract from the activations
        self.maxv = maxv                                  ### maximum allowed value of the activations

    def forward(self, x):
        x = F.leaky_relu(input=x, negative_slope=self.leak) if self.leak is not None else F.relu(input=x)
        if self.sub is not None:
            x.sub_(self.sub)
        if self.maxv is not None:
            x.clamp_max_(self.maxv)
        return x

def init_cnn(model, uniform=False):
    func = init.kaiming_uniform_ if uniform else init.kaiming_normal_
    for layer in model:
        if isinstance(layer, torch.nn.Sequential):
            func(layer[0].weight, a=0.1)                   ### initializing only the conv layer not the ReLU layer
            layer[0].bias.data.zero_()                     ### zeroing the bias of the conv layer

def get_cnn_model(data, nfs, layer, **kwargs):
    return torch.nn.Sequential(*get_cnn_layers(data, nfs, layer, **kwargs))



def get_learn_run(data, nfs, lr, layer, cbs=None, opt_func=None, uniform=False, **kwargs):
    model = get_cnn_model(data, nfs, layer, **kwargs)
    init_cnn(model, uniform=uniform)
    return get_runner(model, data, lr=lr, cbs=cbs, opt_func=opt_func)


from IPython.display import display, Javascript
def nb_auto_export():
    display(Javascript("""{
const ip = IPython.notebook
if (ip) {
    ip.save_notebook()
    console.log('a')
    const s = `!python notebook2script.py ${ip.notebook_name}`
    if (ip.kernel) { ip.kernel.execute(s) }
}
}"""))