import torch
import torchvision.models as models

class FeatureExtractor(torch.nn.Module):
    """Wraps a pretrained ResNet-50 to output a 1×2048 feature vector."""
    def __init__(self):
        super().__init__()
        backbone = models.resnet50(pretrained=True)
        self.features = torch.nn.Sequential(*list(backbone.children())[:-1])

    def forward(self, x):
        x = self.features(x)              # (B,2048,1,1)
        return x.view(x.size(0), -1)     # (B,2048)