from torch import nn
import torch


class ADD(nn.Module):
    def __init__(self, c_x, c_att, c_id):
        super(ADD, self).__init__()

        self.c_x = c_x

        self.h_conv = nn.Conv2d(in_channels=c_x, out_channels=1, kernel_size=1, stride=1, padding=0, bias=True)

        self.att_conv1 = nn.Conv2d(in_channels=c_att, out_channels=c_x, kernel_size=1, stride=1, padding=0, bias=True)
        self.att_conv2 = nn.Conv2d(in_channels=c_att, out_channels=c_x, kernel_size=1, stride=1, padding=0, bias=True)

        self.id_fc1 = nn.Linear(c_id, c_x)
        self.id_fc2 = nn.Linear(c_id, c_x)

        self.norm = nn.InstanceNorm2d(c_x, affine=False)

    def forward(self, h, z_att, z_id):
        h_norm = self.norm(h)

        att_beta = self.att_conv1(z_att)
        att_gamma = self.att_conv2(z_att)

        id_beta = self.id_fc1(z_id)
        id_gamma = self.id_fc2(z_id)

        id_beta = id_beta.reshape(h_norm.shape[0], self.c_x, 1, 1).expand_as(h_norm)
        id_gamma = id_gamma.reshape(h_norm.shape[0], self.c_x, 1, 1).expand_as(h_norm)

        M = torch.sigmoid(self.h_conv(h_norm))
        A = att_gamma * h_norm + att_beta
        I = id_gamma * h_norm + id_beta

        return (torch.ones_like(M).to(M.device) - M) * A + M * I


def conv(c_in, c_out):
    return nn.Sequential(
        nn.ReLU(inplace=True),
        nn.Conv2d(in_channels=c_in, out_channels=c_out, kernel_size=3, stride=1, padding=1, bias=False),
    )


class ADDResBlk(nn.Module):
    def __init__(self, c_in, c_out, c_att, c_id):
        super(ADDResBlk, self).__init__()

        self.c_in = c_in
        self.c_out = c_out

        self.add1 = ADD(c_in, c_att, c_id)
        self.conv1 = conv(c_in, c_in)
        self.add2 = ADD(c_in, c_att, c_id)
        self.conv2 = conv(c_in, c_out)

        if c_in != c_out:
            self.add3 = ADD(c_in, c_att, c_id)
            self.conv3 = conv(c_in, c_out)

    def forward(self, h, z_att, z_id):
        x = self.add1(h, z_att, z_id)
        x = self.conv1(x)
        x = self.add1(x, z_att, z_id)
        x = self.conv2(x)
        if self.c_in != self.c_out:
            h = self.add3(h, z_att, z_id)
            h = self.conv3(h)

        return x + h


# import torch
# import torch.nn as nn


# class AADLayer(nn.Module):
#     def __init__(self, c_x, attr_c, c_id=256):
#         super(AADLayer, self).__init__()
#         self.attr_c = attr_c
#         self.c_id = c_id
#         self.c_x = c_x

#         self.conv1 = nn.Conv2d(attr_c, c_x, kernel_size=1, stride=1, padding=0, bias=True)
#         self.conv2 = nn.Conv2d(attr_c, c_x, kernel_size=1, stride=1, padding=0, bias=True)
#         self.fc1 = nn.Linear(c_id, c_x)
#         self.fc2 = nn.Linear(c_id, c_x)
#         self.norm = nn.InstanceNorm2d(c_x, affine=False)

#         self.conv_h = nn.Conv2d(c_x, 1, kernel_size=1, stride=1, padding=0, bias=True)

#     def forward(self, h_in, z_attr, z_id):
#         # h_in cxnxn
#         # zid 256x1x1
#         # zattr cxnxn
#         h = self.norm(h_in)
#         gamma_attr = self.conv1(z_attr)
#         beta_attr = self.conv2(z_attr)

#         gamma_id = self.fc1(z_id)
#         beta_id = self.fc2(z_id)
#         A = gamma_attr * h + beta_attr
#         gamma_id = gamma_id.reshape(h.shape[0], self.c_x, 1, 1).expand_as(h)
#         beta_id = beta_id.reshape(h.shape[0], self.c_x, 1, 1).expand_as(h)
#         I = gamma_id * h + beta_id

#         M = torch.sigmoid(self.conv_h(h))

#         out = (torch.ones_like(M).to(M.device) - M) * A + M * I
#         return out


# class ADDResBlk(nn.Module):
#     def __init__(self, cin, cout, c_attr, c_id=256):
#         super(ADDResBlk, self).__init__()
#         self.cin = cin
#         self.cout = cout

#         self.AAD1 = AADLayer(cin, c_attr, c_id)
#         self.conv1 = nn.Conv2d(cin, cin, kernel_size=3, stride=1, padding=1, bias=False)
#         self.relu1 = nn.ReLU(inplace=True)

#         self.AAD2 = AADLayer(cin, c_attr, c_id)
#         self.conv2 = nn.Conv2d(cin, cout, kernel_size=3, stride=1, padding=1, bias=False)
#         self.relu2 = nn.ReLU(inplace=True)

#         if cin != cout:
#             self.AAD3 = AADLayer(cin, c_attr, c_id)
#             self.conv3 = nn.Conv2d(cin, cout, kernel_size=3, stride=1, padding=1, bias=False)
#             self.relu3 = nn.ReLU(inplace=True)

#     def forward(self, h, z_attr, z_id):
#         x = self.AAD1(h, z_attr, z_id)
#         x = self.relu1(x)
#         x = self.conv1(x)

#         x = self.AAD2(x,z_attr, z_id)
#         x = self.relu2(x)
#         x = self.conv2(x)

#         if self.cin != self.cout:
#             h = self.AAD3(h, z_attr, z_id)
#             h = self.relu3(h)
#             h = self.conv3(h)
#         x = x + h
        
#         return x


