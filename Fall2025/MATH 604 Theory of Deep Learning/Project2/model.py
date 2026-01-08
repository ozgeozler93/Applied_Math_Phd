import torch
import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.block(x)

class UpConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.up = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True),
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.up(x)

class AttentionBlock(nn.Module):
    def __init__(self, F_g, F_l, F_int):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(F_int)
        )

        self.W_x = nn.Sequential(
            nn.Conv2d(F_l, F_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(F_int)
        )

        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )

        self.relu = nn.ReLU(inplace=True)

    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        return x * psi

class AttentionUNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()
        # Encoder
        self.conv1 = ConvBlock(in_channels, 64)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = ConvBlock(64, 128)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv3 = ConvBlock(128, 256)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv4 = ConvBlock(256, 512)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.bottleneck = ConvBlock(512, 1024)

        # Decoder
        self.up4 = UpConv(1024, 512)
        self.att4 = AttentionBlock(F_g=512, F_l=512, F_int=256)
        self.conv_up4 = ConvBlock(1024, 512)

        self.up3 = UpConv(512, 256)
        self.att3 = AttentionBlock(F_g=256, F_l=256, F_int=128)
        self.conv_up3 = ConvBlock(512, 256)

        self.up2 = UpConv(256, 128)
        self.att2 = AttentionBlock(F_g=128, F_l=128, F_int=64)
        self.conv_up2 = ConvBlock(256, 128)

        self.up1 = UpConv(128, 64)
        self.att1 = AttentionBlock(F_g=64, F_l=64, F_int=32)
        self.conv_up1 = ConvBlock(128, 64)

        self.final_conv = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x):
        # Encoder
        x1 = self.conv1(x)
        x2 = self.pool1(x1)
        x2 = self.conv2(x2)
        x3 = self.pool2(x2)
        x3 = self.conv3(x3)
        x4 = self.pool3(x3)
        x4 = self.conv4(x4)
        x5 = self.pool4(x4)

        # Bottleneck
        x5 = self.bottleneck(x5)

        # Decoder
        d4 = self.up4(x5)
        x4_att = self.att4(g=d4, x=x4)
        d4 = torch.cat((x4_att, d4), dim=1)
        d4 = self.conv_up4(d4)

        d3 = self.up3(d4)
        x3_att = self.att3(g=d3, x=x3)
        d3 = torch.cat((x3_att, d3), dim=1)
        d3 = self.conv_up3(d3)

        d2 = self.up2(d3)
        x2_att = self.att2(g=d2, x=x2)
        d2 = torch.cat((x2_att, d2), dim=1)
        d2 = self.conv_up2(d2)

        d1 = self.up1(d2)
        x1_att = self.att1(g=d1, x=x1)
        d1 = torch.cat((x1_att, d1), dim=1)
        d1 = self.conv_up1(d1)

        return self.final_conv(d1)

if __name__ == '__main__':
    model = AttentionUNet(in_channels=3, out_channels=1)
    dummy_input = torch.randn(1, 3, 256, 256)
    output = model(dummy_input)
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")