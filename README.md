# Automatically Detect Dices 

 Dice detector BOX, from Zurich University of Applied Sciences (ZHAW).
 In development!

A project to display Computer Vision Machine Learning and Statistics in a playful way 

![image](https://github.com/buehlpa/Dice/assets/64488738/46b51cfd-4974-4864-b354-d0685827d79d)


### Current UI
![image](https://github.com/buehlpa/Dice/assets/64488738/d801b7f3-2cf3-420e-bab1-dad99851a578)

## Installation on UNIX

- clone Repo
- create conda env 

```
conda create -n dice python=3.9.18
```
or
```
python -m venv /path/to/new/virtual/environment
```

```
pip install -r requirements_unix.txt
```


please download the pretrained models from https://www.mydrive.ch/download/452498811-1699782892/models.rar and put the models here:
```
Dice/raspberry_run/models/
```


## Hints
Dice/raspberry_run  - this directory contains the code to run on the rasperry PI with limited resources, the core is developed in /workspace 

```
Dice/raspberry_run/main.py 
```           
is the functioning version , please develop in the *_dev.py files

run with 
```
C:\Users\USER\repos\Dice\raspberry_run> python main.py
```     



Dice/workspace  - train DL models  on machine with gpu 
                - state detector
                - dice side detector 

            - develop Algos to detect dices 
                - greenscreen , eroding, masking etc. 
                
                
                
                
# Fixing tflite:

tflite runtime with

pip install tensorflow

..
