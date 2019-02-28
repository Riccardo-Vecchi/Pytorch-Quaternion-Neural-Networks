##########################################################
# pytorch-qnn v1.0                                     
# Titouan Parcollet
# LIA, Université d'Avignon et des Pays du Vaucluse
# ORKIS, Aix-en-provence
# October 2018
##########################################################

from torch.nn import Module
from torch.nn.parameter import Parameter

from quaternion_ops import *


class QuaternionTransposeConv(Module):
    r"""Applies a Quaternion Transposed Convolution (or Deconvolution) to the incoming data.
    """

    def __init__(self, in_channels, out_channels, kernel_size, stride,
                 dilatation=1, padding=0, output_padding=0, groups=1, bias=True, init_criterion='glorot',
                 weight_init='quaternion', seed=None, operation='convolution2d', rotation=False):

        super(QuaternionTransposeConv, self).__init__()

        self.in_channels = in_channels // 4
        self.out_channels = out_channels // 4
        self.stride = stride
        self.padding = padding
        self.output_padding = output_padding
        self.groups = groups
        self.dilatation = dilatation
        self.init_criterion = init_criterion
        self.weight_init = weight_init
        self.seed = seed if seed is not None else 1234
        self.rng = RandomState(self.seed)
        self.operation = operation
        self.rotation = rotation
        self.winit = {'quaternion': quaternion_init,
                      'unitary': unitary_init,
                      'random': random_init}[self.weight_init]

        (self.kernel_size, self.w_shape) = get_kernel_and_weight_shape(self.operation,
                                                                       self.out_channels, self.in_channels, kernel_size)

        self.r_weight = Parameter(torch.Tensor(*self.w_shape))
        self.i_weight = Parameter(torch.Tensor(*self.w_shape))
        self.j_weight = Parameter(torch.Tensor(*self.w_shape))
        self.k_weight = Parameter(torch.Tensor(*self.w_shape))

        if bias:
            self.bias = Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        affect_init_conv(self.r_weight, self.i_weight, self.j_weight, self.k_weight,
                         self.kernel_size, self.winit, self.rng, self.init_criterion)
        if self.bias is not None:
            self.bias.data.zero_()

    def forward(self, input):

        if self.rotation:
            return quaternion_transpose_conv_rotation(input, self.r_weight, self.i_weight,
                                                      self.j_weight, self.k_weight, self.bias, self.stride,
                                                      self.padding,
                                                      self.output_padding, self.groups, self.dilatation)
        else:
            return quaternion_transpose_conv(input, self.r_weight, self.i_weight, self.j_weight,
                                             self.k_weight, self.bias, self.stride, self.padding, self.output_padding,
                                             self.groups, self.dilatation)

    def __repr__(self):
        return self.__class__.__name__ + '(' \
               + 'in_channels=' + str(self.in_channels) \
               + ', out_channels=' + str(self.out_channels) \
               + ', bias=' + str(self.bias is not None) \
               + ', kernel_size=' + str(self.kernel_size) \
               + ', stride=' + str(self.stride) \
               + ', padding=' + str(self.padding) \
               + ', dilation=' + str(self.dilation) \
               + ', init_criterion=' + str(self.init_criterion) \
               + ', weight_init=' + str(self.weight_init) \
               + ', seed=' + str(self.seed) \
               + ', operation=' + str(self.operation) + ')'


class QuaternionConv(Module):
    r"""Applies a Quaternion Convolution to the incoming data.
    """

    def __init__(self, in_channels, out_channels, kernel_size, stride,
                 dilatation=1, padding=0, groups=1, bias=True, init_criterion='glorot',
                 weight_init='quaternion', seed=None, operation='convolution2d', rotation=False):

        super(QuaternionConv, self).__init__()

        self.in_channels = in_channels // 4
        self.out_channels = out_channels // 4
        self.stride = stride
        self.padding = padding
        self.groups = groups
        self.dilatation = dilatation
        self.init_criterion = init_criterion
        self.weight_init = weight_init
        self.seed = seed if seed is not None else 1234
        self.rng = RandomState(self.seed)
        self.operation = operation
        self.rotation = rotation
        self.winit = {'quaternion': quaternion_init,
                      'unitary': unitary_init,
                      'random': random_init}[self.weight_init]

        (self.kernel_size, self.w_shape) = get_kernel_and_weight_shape(self.operation,
                                                                       self.in_channels, self.out_channels, kernel_size)

        self.r_weight = Parameter(torch.Tensor(*self.w_shape))
        self.i_weight = Parameter(torch.Tensor(*self.w_shape))
        self.j_weight = Parameter(torch.Tensor(*self.w_shape))
        self.k_weight = Parameter(torch.Tensor(*self.w_shape))

        if bias:
            self.bias = Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        affect_init_conv(self.r_weight, self.i_weight, self.j_weight, self.k_weight,
                         self.kernel_size, self.winit, self.rng, self.init_criterion)
        if self.bias is not None:
            self.bias.data.zero_()

    def forward(self, input):

        if self.rotation:
            return quaternion_conv_rotation(input, self.r_weight, self.i_weight, self.j_weight,
                                            self.k_weight, self.bias, self.stride, self.padding, self.groups,
                                            self.dilatation)
        else:
            return quaternion_conv(input, self.r_weight, self.i_weight, self.j_weight,
                                   self.k_weight, self.bias, self.stride, self.padding, self.groups, self.dilatation)

    def __repr__(self):
        return self.__class__.__name__ + '(' \
               + 'in_channels=' + str(self.in_channels) \
               + ', out_channels=' + str(self.out_channels) \
               + ', bias=' + str(self.bias is not None) \
               + ', kernel_size=' + str(self.kernel_size) \
               + ', stride=' + str(self.stride) \
               + ', padding=' + str(self.padding) \
               + ', dilation=' + str(self.dilation) \
               + ', init_criterion=' + str(self.init_criterion) \
               + ', weight_init=' + str(self.weight_init) \
               + ', seed=' + str(self.seed) \
               + ', operation=' + str(self.operation) + ')'


class QuaternionLinearAutograd(Module):
    r"""Applies a quaternion linear transformation to the incoming data. A custom
    Autograd function is call to drastically reduce the VRAM consumption. Nonetheless, computing
    time is also slower compared to QuaternionLinear().
    """

    def __init__(self, in_features, out_features, bias=True,
                 init_criterion='glorot', weight_init='quaternion',
                 seed=None, rotation=False):

        super(QuaternionLinearAutograd, self).__init__()
        self.in_features = in_features // 4
        self.out_features = out_features // 4
        self.rotation = rotation
        self.r_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        self.i_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        self.j_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        self.k_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        if bias:
            self.bias = Parameter(torch.Tensor(self.out_features * 4))
        else:
            self.register_parameter('bias', None)
        self.init_criterion = init_criterion
        self.weight_init = weight_init
        self.seed = seed if seed is not None else 1337
        self.rng = RandomState(self.seed)
        self.reset_parameters()

    def reset_parameters(self):
        winit = {'quaternion': quaternion_init, 'unitary': unitary_init, 'random': random_init}[self.weight_init]
        if self.bias is not None:
            self.bias.data.fill_(0)
        affect_init(self.r_weight, self.i_weight, self.j_weight, self.k_weight, winit,
                    self.rng, self.init_criterion)

    def forward(self, input):
        # See the autograd section for explanation of what happens here.
        if self.rotation:
            return quaternion_linear_rotation(input, self.r_weight, self.i_weight, self.j_weight, self.k_weight,
                                              self.bias)
        else:
            return quaternion_linear(input, self.r_weight, self.i_weight, self.j_weight, self.k_weight, self.bias)

    def __repr__(self):
        return self.__class__.__name__ + '(' \
               + 'in_features=' + str(self.in_features) \
               + ', out_features=' + str(self.out_features) \
               + ', bias=' + str(self.bias is not None) \
               + ', init_criterion=' + str(self.init_criterion) \
               + ', weight_init=' + str(self.weight_init) \
               + ', seed=' + str(self.seed) + ')'


class QuaternionLinear(Module):
    r"""Applies a quaternion linear transformation to the incoming data.
    """

    def __init__(self, in_features, out_features, bias=True,
                 init_criterion='glorot', weight_init='quaternion',
                 seed=None):

        super(QuaternionLinear, self).__init__()
        self.in_features = in_features // 4
        self.out_features = out_features // 4
        self.r_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        self.i_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        self.j_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        self.k_weight = Parameter(torch.Tensor(self.in_features, self.out_features))
        if bias:
            self.bias = Parameter(torch.Tensor(self.out_features * 4))
        else:
            self.register_parameter('bias', None)
        self.init_criterion = init_criterion
        self.weight_init = weight_init
        self.seed = seed if seed is not None else 1337
        self.rng = RandomState(self.seed)
        self.reset_parameters()

    def reset_parameters(self):
        winit = {'quaternion': quaternion_init,
                 'unitary': unitary_init}[self.weight_init]
        if self.bias is not None:
            self.bias.data.fill_(0)
        affect_init(self.r_weight, self.i_weight, self.j_weight, self.k_weight, winit,
                    self.rng, self.init_criterion)

    def forward(self, input):
        # See the autograd section for explanation of what happens here.
        if input.dim() == 3:
            T, N, C = input.size()
            input = input.view(T * N, C)
            output = QuaternionLinearFunction.apply(input, self.r_weight, self.i_weight, self.j_weight, self.k_weight,
                                                    self.bias)
            output = output.view(T, N, output.size(1))
        elif input.dim() == 2:
            output = QuaternionLinearFunction.apply(input, self.r_weight, self.i_weight, self.j_weight, self.k_weight,
                                                    self.bias)
        else:
            raise NotImplementedError

        return output

    def __repr__(self):
        return self.__class__.__name__ + '(' \
               + 'in_features=' + str(self.in_features) \
               + ', out_features=' + str(self.out_features) \
               + ', bias=' + str(self.bias is not None) \
               + ', init_criterion=' + str(self.init_criterion) \
               + ', weight_init=' + str(self.weight_init) \
               + ', seed=' + str(self.seed) + ')'
