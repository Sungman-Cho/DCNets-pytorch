import torch
import torch.nn as nn
import torch.nn.functional as F

class Conv2d(nn.Module):
    def __init__(self, in_ch, out_ch, k_size, stride=1, padding=1, magnitude=None, angular=None):
        super(Conv2d, self).__init__()
        self.in_ch = in_ch
        self.out_ch = out_ch
        self.stride = stride
        self.padding = padding
        self.k_size = k_size
        self.kernel = self._get_conv_filter(out_ch, in_ch, k_size)
        self.eps = 1e-4

        self.magnitude = magnitude
        self.angular = angular
    
    def _get_conv_filter(self, out_ch, in_ch, k_size):
        kernel = nn.Parameter(torch.Tensor(out_ch, in_ch, k_size, k_size))
        
        # weight intialization
        kernel = nn.init.kaiming_normal_(kernel)
        return kernel
    
    def _get_filter_norm(self, kernel):
        return torch.norm(kernel.data, 2, 1, True)
    
    def _get_input_norm(self, feat):
        f = torch.ones(1, self.in_ch, self.k_size, self.k_size)
        input_norm = torch.sqrt(F.conv2d(feat*feat, f, stride=self.stride, padding=self.padding)+self.eps)
        return input_norm
    
    #TODO: add orthogonal constraint
    '''
    def _add_orthogonal_constraint(self):
    '''

    def forward(self, x):
        if self.magnitude is None:
            out = F.conv2d(x, self.kernel, stride=self.stride, padding=self.padding)

        elif self.magnitude == "ball":
            
            x_norm = self._get_input_norm(x) 
            w_norm = self._get_filter_norm(self.kernel)
            
            kernel_tensor = nn.utils.parameters_to_vector(self.kernel)
            kernel_tensor = torch.reshape(kernel_tensor,self.kernel.shape)
            kernel_tensor = kernel_tensor / w_norm
            
            out = F.conv2d(x, kernel_tensor, stride=self.stride, padding=self.padding)

            radius = nn.Parameter(torch.Tensor(out.shape[0], 1, 1, 1))
            radius = nn.init.constant_(radius, 1.0) ** 2 + self.eps
            
            min_x_radius = torch.min(x_norm, radius)

            out = (out / x_norm) * (min_x_radius / radius)


        elif self.magnitude == "linear":
            
            x_norm = self._get_input_norm(x) 
            w_norm = self._get_filter_norm(self.kernel)
            
            kernel_tensor = nn.utils.parameters_to_vector(self.kernel)
            kernel_tensor = torch.reshape(kernel_tensor,self.kernel.shape)
            kernel_tensor = kernel_tensor / w_norm
            
            out = F.conv2d(x, kernel_tensor, stride=self.stride, padding=self.padding)
        
        elif self.magnitude == "sphere":
            x_norm = self._get_input_norm(x) 
            w_norm = self._get_filter_norm(self.kernel)
            
            kernel_tensor = nn.utils.parameters_to_vector(self.kernel)
            kernel_tensor = torch.reshape(kernel_tensor,self.kernel.shape)
            kernel_tensor = kernel_tensor / w_norm
            
            out = F.conv2d(x, kernel_tensor, stride=self.stride, padding=self.padding)
            out = out / x_norm 

        else:
            out = None

        return out


class DCNet(nn.Module):
    def __init__(self, magnitude, angular):
        super(DCNet, self).__init__()
        
        self.features = nn.Sequential(
                Conv2d(in_ch=1, out_ch=6, k_size=5, magnitude=magnitude),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=(2,2), stride=2),
                Conv2d(in_ch=6, out_ch=16, k_size=5, magnitude=magnitude),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=(2,2), stride=2),
                Conv2d(in_ch=16, out_ch=120, k_size=5, magnitude=magnitude),
                nn.ReLU()
                )
        
        self.fc1 = nn.Linear(1080, 512)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(512, 10)
        
        self.embeddings = None
    
    def forward(self, x):
        x = self.features(x) 
        x = x.view(x.size(0), -1)
        self.embeddings = self.fc1(x)
        x = self.relu(self.embeddings)
        x = self.fc2(x)

        return x

    def get_features(self):
        return self.embeddings
        
            
if __name__ == '__main__':
    net = DCNet()

    x = torch.randn([1,3,3,3])
    y = net(x)


