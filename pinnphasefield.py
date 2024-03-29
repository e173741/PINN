import tensorflow as tf
tf.compat.v1.enable_eager_execution()
import numpy as np
import matplotlib.pyplot as plt
import scipy.io
from scipy.interpolate import griddata
import time
from tensorflow.keras import Model
from tensorflow import keras
from tensorflow.keras import layers

from google.colab import drive
drive.mount("/content/drive")

!pip install mat73
import mat73

S1=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/edgeinput_6.mat')
 S2=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/nodeinput_6.mat')
 S3=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/nodeoutput_6.mat')
 S4=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/damageinput_6.mat')
 S5=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/damageoutput_6.mat')
 S6=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/G1_6.mat')
 S7=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/G2_6.mat')
 S8=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/coord_6.mat')
 S9=mat73.loadmat('/content/drive/MyDrive/Colab Notebooks/experiment/nodeinputstr_6.mat')

edgeinput=S1['edgeinputfeature']
nodeinput=S2['nodeinputfeature']
nodeinputstr=S9['nodeinputfeaturestr']
nodeoutput=S3['nodeoutputfeature']
damageinput=S4['damageinput']
damageoutput=S5['damageoutput']
G1=S6['G1']
G2=S7['G2']
coord=S8['coord']

cord=coord
prop=edgeinput
field=damageinput
sigma_true=nodeinput
strain_true=nodeinputstr

modulus=np.zeros((6,1))
shear_modulus=modulus 
lc=modulus
fracture_energy1=modulus
fracture_energy2=modulus
c=modulus
friction=modulus

for i in range(6) :
 modulus[i]=prop[i][0][0][0]
 shear_modulus[i]=prop[i][0][0][0]/2.5
 lc[i]=prop[i][0][0][1]
 fracture_energy2[i]=prop[i][0][0][2]
 c[i]=prop[i][0][0][4]
 friction[i]=prop[i][0][0][3]

x = [[0 for i in range(np.array(coord[j]).shape[1])] for j in range(6)]
y=x
for i in range(6) :
  
 for j in range(np.array(coord[i]).shape[1]) :
  x[i][j]=coord[i][0][j]
  y[i][j]=coord[i][1][j]

modulus3=tf.convert_to_tensor(modulus, dtype=tf.float32)
shear_modulus=tf.convert_to_tensor(shear_modulus, dtype=tf.float32)
lc=tf.convert_to_tensor(lc, dtype=tf.float32)
fracture_energy1=tf.convert_to_tensor(fracture_energy1, dtype=tf.float32)
fracture_energy2=tf.convert_to_tensor(fracture_energy2, dtype=tf.float32)
c=tf.convert_to_tensor(c, dtype=tf.float32)
friction=tf.convert_to_tensor(friction, dtype=tf.float32)

def base_graph(i,j) :
        load=tf.convert_to_tensor(G1[i][0],dtype=tf.float32) #0
        boundary=tf.convert_to_tensor(G2[i][0],dtype=tf.float32) #1
        x1=tf.convert_to_tensor(x[i] ,dtype=tf.float32) #2
        y1=tf.convert_to_tensor(y[i],dtype=tf.float32) #3
        field1=tf.convert_to_tensor(field[i][j],dtype=tf.float32) #4
        modulus1=modulus3[i] #5
        shear_modulus1=shear_modulus[i] #6
        sigma_true1=tf.convert_to_tensor(sigma_true[i][j],dtype=tf.float32) #7
        strain_true1=tf.convert_to_tensor(strain_true[i][j],dtype=tf.float32) #7
        fracture_energy21=fracture_energy2[i] #8
        lc1=lc[i] #9
        c1=c[i] #10
        friction1=friction[i] #11  
        cord2=tf.stack([x1,y1],1)
        cord2=tf.reshape(cord2,shape=(x1.shape[0],2)) #12
        load=tf.reshape(load,shape=(x1.shape[0],1))
        boundary=tf.reshape(boundary,shape=(x1.shape[0],1))
        field1=tf.reshape(field1,shape=(x1.shape[0],1))
        x1=tf.reshape(x1,shape=(x1.shape[0],1))
        y1=tf.reshape(y1,shape=(x1.shape[0],1))
        f0=tf.constant(1,dtype=tf.float32)  
        f1=tf.subtract(f0,field1)
        f2=tf.multiply(modulus1,tf.pow(f1,2))
        input4=tf.multiply(fracture_energy21,lc1)
        input5=tf.divide(fracture_energy21,lc1)
        return load,boundary,x1,y1,field1,modulus1,shear_modulus1,sigma_true1,fracture_energy21,lc1,c1,friction1,cord2,f2,input4,input5,strain_true1
tf_dict= [[base_graph(i,j) for j in range(44)] for i in range(5)]

def Hcalculator(stressx,stressy,stressxy,c3,friction3):
    
    sigma11,sigma33=eigen(stressx,stressy,stressxy)
    wc1=tf.divide(tf.subtract(sigma11,sigma33),tf.math.cos(friction3))
    wc2=tf.multiply(tf.add(sigma11,sigma33),tf.math.tan(friction3))
    wc3=tf.subtract(tf.add(wc1,wc2),c3)
    wc4=tf.math.maximum(wc3,tf.constant(0,dtype=tf.float32)) 
    wc=tf.math.square(wc4)
    H=wc
  
    return H 
     
       
def eigen(stressx,stressy,stressxy):
    mean_stress=tf.multiply(0.5,tf.add(stressx,stressy))
    radius1=tf.pow(tf.multiply(0.5,tf.subtract(stressx,stressy)),2)
    radius2=tf.pow(stressxy,2)
    radius=tf.pow(tf.add(radius1,radius2),0.5)
    sigma11=tf.add(mean_stress,radius)
    sigma33=tf.subtract(mean_stress,radius)
                 
    return sigma11,sigma33

firstlayer=30
secondlayer=30
thirdlayer=30
fourthlayer=20

sigma1=tf.keras.layers.Input(shape=(3,))
cordx=tf.keras.layers.Input(shape=(1,))
cordy=tf.keras.layers.Input(shape=(1,))
f2=tf.keras.layers.Input(shape=(1,))
load1=tf.keras.layers.Input(shape=(1,))
boundary1=tf.keras.layers.Input(shape=(1,))

a1=tf.keras.layers.Dense(3,activation='tanh',use_bias=True)(sigma1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)


x2x=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordx)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)


x2y=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordy)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)

x2=tf.keras.layers.Multiply()([x2x,x2y])  

x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(f2)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
   
x4=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(load1)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
   
k=tf.keras.layers.Multiply()([x2,x3])
fint=tf.keras.layers.Multiply()([a1,x2])
fdelta=tf.keras.layers.Multiply()([tf.keras.layers.Multiply()([x4,x2]),x3])
ftot=tf.keras.layers.Add()([fint,fdelta])
x5=tf.keras.layers.Multiply()([k,ftot])
x6=tf.keras.layers.Dense(fourthlayer,activation='tanh',use_bias=True)(x5)
x6=tf.keras.layers.BatchNormalization()(x6)
x7=tf.keras.layers.Dense(fourthlayer,activation='tanh',use_bias=True)(x5)
x7=tf.keras.layers.BatchNormalization()(x7)
x61=tf.keras.layers.Multiply()([x6,boundary1])
ux=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x61)
x71=tf.keras.layers.Multiply()([x7,boundary1])
uy=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x71)


model1=Model(inputs=[sigma1,cordx,cordy,f2,load1,boundary1],outputs=[ux,uy])

def gradient2(sigma1,x11,y11,modulus1,shear_modulus1,field2,c2,friction1,load1,boundary1,H0) :
   f0=tf.constant(1,dtype=tf.float32)
   f1=tf.subtract(f0,field2)
   f2=tf.multiply(modulus1,tf.pow(f1,2))
   dmodulus=tf.multiply(modulus1,tf.pow(f1,2))
   dshear=tf.multiply(shear_modulus1,tf.pow(f1,2))
   with tf.GradientTape(persistent=True) as t2 :
     with tf.GradientTape(persistent=True) as t1 :
      t1.watch(x11)
      t1.watch(y11)
      t2.watch(x11)
      t2.watch(y11)
      ux,uy=model1(inputs=[sigma1,x11,y11,f2,load1,boundary1])
      strainy=t1.gradient(uy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
      strainx=t1.gradient(ux, x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
      strainxy=tf.multiply(tf.constant(0.5,dtype=tf.float32),tf.add(t1.gradient(ux,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO),t1.gradient(uy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)))
      stressy=tf.add(tf.multiply(dmodulus,strainy),tf.multiply(tf.multiply(dmodulus,tf.constant(0.3,dtype=tf.float32)),strainx))
      stressx=tf.add(tf.multiply(dmodulus,strainx),tf.multiply(tf.multiply(dmodulus,tf.constant(0.3,dtype=tf.float32)),strainy))  
      stressxy=tf.multiply(dshear,tf.multiply(tf.constant(0.5,dtype=tf.float32),tf.add(t1.gradient(ux,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO),t1.gradient(uy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO))))
   stressxx=t2.gradient(stressx,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressyy=t2.gradient(stressy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressxyx=t2.gradient(stressxy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressxyy=t2.gradient(stressxy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   strainx=tf.reshape(strainx,shape=(x11.shape[0],1))
   strainy=tf.reshape(strainy,shape=(x11.shape[0],1))
   strainxy=tf.reshape(strainxy,shape=(x11.shape[0],1))
   strain_pred=tf.stack([strainx,strainy,strainxy],1)
   strain_pred=tf.reshape(strain_pred,shape=(x11.shape[0],3))
   stressx=tf.reshape(stressx,shape=(x11.shape[0],1))
   stressy=tf.reshape(stressy,shape=(x11.shape[0],1))
   stressxy=tf.reshape(stressxy,shape=(x11.shape[0],1)) 
   sigma_pred=tf.stack([stressx,stressy,stressxy],1)
   sigma_pred=tf.reshape(sigma_pred,shape=(x11.shape[0],3))
   H=Hcalculator(stressx,stressy,stressxy,c2,friction1)
   return stressxx,stressyy,stressxyx,stressxyy,sigma_pred,H,strain_pred

cordx=tf.keras.layers.Input(shape=(1,))
cordy=tf.keras.layers.Input(shape=(1,))
H=tf.keras.layers.Input(shape=(1,))
field2=tf.keras.layers.Input(shape=(1,))
input4=tf.keras.layers.Input(shape=(1,))
input5=tf.keras.layers.Input(shape=(1,))

x0=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordx)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)

y1=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordy)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)

x1=tf.keras.layers.Multiply()([x0,y1])

x2=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(H)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)

x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(field2)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)

x4=tf.keras.layers.Multiply()([input4,x1])
x5=tf.keras.layers.Multiply()([x2,x1])
x6=tf.keras.layers.Multiply()([input5,x1])
x7=tf.keras.layers.Add()([tf.keras.layers.Add()([x4,x5]),x6])
x8=tf.keras.layers.Multiply()([input5,x3])
x9=tf.keras.layers.Subtract()([tf.keras.layers.Multiply()([x2,x3]),x2])
x10=tf.keras.layers.Add()([tf.keras.layers.Add()([input4,x8]),x9])
x11=tf.keras.layers.Multiply()([x10,x1])
field_predict=tf.keras.layers.Multiply()([x7,x11])

model2 = Model(inputs=[cordx,cordy,H,field2,input4,input5], outputs=[field_predict])

def gradient(x11,y11,H,field2,input4,input5) :

 with tf.GradientTape(persistent=True) as t3 :
      with tf.GradientTape(persistent=True) as t4 :
         t3.watch(x11)
         t3.watch(y11)
         t4.watch(x11)
         t4.watch(y11)
         field_predict=model2(inputs=[x11,y11,H,field2,input4,input5])
      fix=t4.gradient(field_predict,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
      fiy=t4.gradient(field_predict,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
 fixx=t3.gradient(fix,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
 fiyy=t3.gradient(fiy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
 return fixx,fiyy

def loss1(sigma_pred,sigma_true):
    loss1=tf.reduce_mean(tf.abs(tf.subtract(sigma_pred,sigma_true)))
        
    return loss1
    
def loss2(fieldpred,fieldtrue) :
      
    loss2=tf.reduce_mean(tf.abs(tf.subtract(fieldpred,fieldtrue)))
    return loss2

def loss3(stressxx,stressyy,stressxyx,stressxyy) : 
    loss3=tf.add(tf.reduce_mean(tf.abs(stressxx+stressxyy)),tf.reduce_mean(tf.abs(stressxyx+stressyy)))
    return loss3

def loss4(fracture_energy25,lc25,field25,H,fixx,fiyy) :
    damage=tf.subtract(tf.constant(1,dtype=tf.float32),field25)
    x1=tf.multiply(tf.divide(fracture_energy25,lc25),field25)
    x2=tf.multiply(tf.multiply(fracture_energy25,lc25),tf.add(fixx,fiyy))
    x3=tf.multiply(tf.constant(2,dtype=tf.float32),tf.multiply(damage,H))
    loss4=tf.abs(tf.reduce_mean(tf.add(tf.subtract(x2,x1),x3)))
    return loss4

def loss5(ux,uy,ux_true,uy_true) :
      
    loss5=tf.add(tf.reduce_mean(tf.math.square(tf.subtract(ux,ux_true))),tf.reduce_mean(tf.math.square(tf.subtract(uy,uy_true))))
    return loss5
def loss6(strain_pred,strain_true):
    loss6=tf.reduce_mean(tf.abs(tf.subtract(strain_pred,strain_true)))
        
    return loss6

def accstress(sigma_pred10,sigma_true10):
    accstress=tf.math.abs(tf.divide(tf.reduce_mean(tf.subtract(sigma_true10,sigma_pred10)),tf.reduce_mean(sigma_true10)))
    return accstress
def accstrain(strain_pred10,strain_true10):
    accstrain=tf.math.abs(tf.divide(tf.reduce_mean(tf.subtract(strain_true10,strain_pred10)),tf.reduce_mean(strain_true10)))
    return accstrain

def accfield(field_pred10,field_true10):
    accfield=tf.math.abs(tf.divide(tf.reduce_sum(field_true10-field_pred10),tf.reduce_sum(field_true10)))
    return accfield
def accdisp(ux,uy,ux_true,uy_true):
    accdisp=tf.math.abs(tf.divide(tf.reduce_mean(tf.subtract(ux,ux_true)),tf.reduce_mean(ux_true)))+tf.math.abs(tf.divide(tf.reduce_mean(tf.subtract(ux,ux_true)),tf.reduce_mean(ux_true)))
    return accdisp

i=0
j=0
output1=model1(inputs=[tf_dict[i][j][7],tf_dict[i][j][2],tf_dict[i][j][3],tf_dict[i][j][13],batch*tf_dict[i][j][0],tf_dict[i][j][1]])
  
output2=gradient2(tf_dict[i][j][7],tf_dict[i][j][2],tf_dict[i][j][3],tf_dict[i][j][5],tf_dict[i][j][6],tf_dict[i][j][4],tf_dict[i][j][10],tf_dict[i][j][11],batch*tf_dict[i][j][0],tf_dict[i][j][1])
  
output3=model2(inputs=[tf_dict[i][j][2],tf_dict[i][j][3],output2[5],tf_dict[i][j][4],tf_dict[i][j][14],tf_dict[i][j][15]])
 
output4=gradient(tf_dict[i][j][2],tf_dict[i][j][3],output2[5],tf_dict[i][j][4],tf_dict[i][j][14],tf_dict[i][j][15])
         
loss_1=loss1(output2[4],tf_dict[i][j+batch][7])
loss_2=loss2(output3,tf_dict[i][j+batch][4])
loss_3=loss3(output2[0],output2[1],output2[2],output2[3])
loss_4=loss4(tf_dict[i][j][8],tf_dict[i][j][9],output3,output2[5],output4[0],output4[1])
loss_5=loss5(output1[0],output1[1],tf_dict[i][j][2],tf_dict[i][j][3])

          
losstotal=loss1(output2[4],tf_dict[i][j+batch][7])+loss2(output3,tf_dict[i][j+batch][4])+loss3(output2[0],output2[1],output2[2],output2[3])+loss4(tf_dict[i][j][8],tf_dict[i][j][9],output3,output2[5],output4[0],output4[1])+loss5(output1[0],output1[1],tf_dict[i][j][2],tf_dict[i][j][3])
               
accuracystress_tr=accstress(output2[4],tf_dict[i][j+batch][7])
accuracyfield_tr=accfield(output3,tf_dict[i][j+batch][4]) 
accuracydisp_tr=accdisp(output1[0],output1[1],tf_dict[i][j][2],tf_dict[i][j][3])

last_iteration = 0
num_training_iterations=100
logged_iterations = []
totalloss_tr1 = []
totalloss_tr2 = []
accuracyst_tr = []
accuracyfi_tr = []
accuracydi_tr = []
loss_1tr=[]
loss_2tr=[]
loss_3tr=[]
loss_4tr=[]
loss_5tr=[]
optimizer1=tf.optimizers.Adam(learning_rate=0.000001)
optimizer2=tf.optimizers.Adam(learning_rate=0.000001)
batch1=np.random.randint(1,5, size=(num_training_iterations))

output3

tf_dict[i][j][16]

for iteration in range(last_iteration, 1000):
 last_iteration = iteration
 batch=5
 for i in range(0,5) :
   
   for j in range(0,43-batch,batch):
       with tf.GradientTape(persistent=True) as tape:

        output1=model1(inputs=[tf_dict[i][j][7],tf_dict[i][j][2],tf_dict[i][j][3],tf_dict[i][j][13],batch*tf_dict[i][j][0],tf_dict[i][j][1]])
   
        output2=gradient2(tf_dict[i][j][7],tf_dict[i][j][2],tf_dict[i][j][3],tf_dict[i][j][5],tf_dict[i][j][6],tf_dict[i][j][4],tf_dict[i][j][10],tf_dict[i][j][11],batch*tf_dict[i][j][0],tf_dict[i][j][1],H)
        
        output3=model2(inputs=[tf_dict[i][j][2],tf_dict[i][j][3],output2[5],tf_dict[i][j][4],tf_dict[i][j][14],tf_dict[i][j][15]])
 
        output4=gradient(tf_dict[i][j][2],tf_dict[i][j][3],output2[5],tf_dict[i][j][4],tf_dict[i][j][14],tf_dict[i][j][15])
         
        loss_1=loss1(output2[4],tf_dict[i][j+batch][7])
        loss_2=loss2(output3,tf_dict[i][j+batch][4])
        loss_3=loss3(output2[0],output2[1],output2[2],output2[3])
        loss_4=loss4(tf_dict[i][j][8],tf_dict[i][j][9],output3,output2[5],output4[0],output4[1])
        loss_6=loss6(output2[6],tf_dict[i][j][16])

          
        losstotal1=loss_1+loss_3+loss_6
        losstotal2=loss_2+loss_4

        accuracystrain_tr=accstrain(output2[6],tf_dict[i][j+batch][16])
        accuracystress_tr=accstress(output2[4],tf_dict[i][j+batch][7])
        accuracyfield_tr=accfield(output3,tf_dict[i][j+batch][4]) 
          
    
    # Calculate gradients
       model_gradients1= tape.gradient(losstotal1,model1.trainable_variables)
       model_gradients2= tape.gradient(losstotal2,model2.trainable_variables)
       
    # Update model
       optimizer1.apply_gradients(zip(model_gradients1,model1.trainable_variables)) 
       optimizer2.apply_gradients(zip(model_gradients2,model2.trainable_variables))


 print("# {:05d},Losstotal1 {:.4f},Losstotal2 {:.4f},Loss1 {:.4f},Loss2 {:.4f},Loss3 {:.4f},Loss4 {:.4f},accstress_tr {:.4f},accfield_tr {:.4f}".format(iteration,losstotal1.numpy(),losstotal2.numpy(),loss_1.numpy(),loss_2.numpy(),loss_3.numpy(),loss_4.numpy(),accuracystress_tr.numpy(),accuracyfield_tr.numpy()))
 totalloss_tr1.append(losstotal1.numpy())
 totalloss_tr2.append(losstotal2.numpy())
 loss_1tr.append(loss_1.numpy())
 loss_2tr.append(loss_2.numpy())
 loss_3tr.append(loss_3.numpy())
 loss_4tr.append(loss_4.numpy())
 
 accuracyst_tr.append(accuracystress_tr.numpy())
 accuracyfi_tr.append(accuracyfield_tr.numpy())

model1.save("/content/drive/MyDrive/Colab Notebooks/experiment/model1PINN.h5")

model2.save("/content/drive/MyDrive/Colab Notebooks/experiment/model2PINN.h5")

from keras import models    
model3 = models.load_model('/content/drive/MyDrive/Colab Notebooks/experiment/graphnetworkmodel.h5')

j

tf.reduce_max(output3)

tf.math.reduce_max(output3)

output2

tf.reduce_max(output2[5])

output1

def gradient2(ux,uy,x11,y11,modulus1,shear_modulus1,field2,c2,friction1) :
   f0=tf.constant(1,dtype=tf.float32)
   f1=tf.subtract(f0,field2)
   with tf.GradientTape(persistent=True) as t1 :
    strainy=t1.gradient(uy, y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
    strainx=t1.gradient(ux, x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)  
    strainxy=tf.transpose(tf.add(t1.gradient(ux,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO),t1.gradient(uy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)))
   damage=f1 
   dmodulus=tf.multiply(damage,modulus1)
   dshear=tf.multiply(damage,shear_modulus1)
   stressx=tf.multiply(dmodulus,tf.transpose(strainx))
   stressy=tf.multiply(dmodulus,tf.transpose(strainy))
   stressxy=tf.multiply(dshear,strainxy)
   stressx=tf.reshape(stressx,shape=(x11.shape[0],1))
   stressy=tf.reshape(stressy,shape=(x11.shape[0],1))
   stressxy=tf.reshape(stressxy,shape=(x11.shape[0],1))
   with tf.GradientTape(persistent=True) as t2 :
    stressxx=t2.gradient(stressx,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
    stressyy=t2.gradient(stressy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
    stressxyx=t2.gradient(stressxy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
    stressxyy=t2.gradient(stressxy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   sigma_pred=tf.stack([stressx,stressy,stressxy],1)
   sigma_pred=tf.reshape(sigma_pred,shape=(x11.shape[0],3))
   H=Hcalculator(stressx,stressy,stressxy,c2,friction1)
   return stressxx,stressyy,stressxyx,stressxyy,sigma_pred,H

def gradient2(ux,uy,x11,y11,modulus1,shear_modulus1,field2,c2,friction1) :
   f0=tf.constant(1,dtype=tf.float32)
   f1=tf.subtract(f0,field2)
   strainy=tf.gradients(uy, y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   strainx=tf.gradients(ux, x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)  
   strainxy=tf.transpose(tf.add(tf.gradients(ux,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO),tf.gradients(uy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)))
   damage=f1 
   dmodulus=tf.multiply(damage,modulus1)
   dshear=tf.multiply(damage,shear_modulus1)
   stressx=tf.multiply(dmodulus,tf.transpose(strainx))
   stressy=tf.multiply(dmodulus,tf.transpose(strainy))
   stressxy=tf.multiply(dshear,strainxy)
   stressx=tf.reshape(stressx,shape=(x11.shape[0],1))
   stressy=tf.reshape(stressy,shape=(x11.shape[0],1))
   stressxy=tf.reshape(stressxy,shape=(x11.shape[0],1))
   stressxx=tf.gradients(stressx,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressyy=tf.gradients(stressy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressxyx=tf.gradients(stressxy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressxyy=tf.gradients(stressxy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   sigma_pred=tf.stack([stressx,stressy,stressxy],1)
   sigma_pred=tf.reshape(sigma_pred,shape=(x11.shape[0],3))
   H=Hcalculator(stressx,stressy,stressxy,c2,friction1)
   return stressxx,stressyy,stressxyx,stressxyy,sigma_pred,H

def gradient2(sigma1,x11,y11,modulus1,shear_modulus1,field2,c2,friction1,load1,boundary1) :
   f0=tf.constant(1,dtype=tf.float32)
   f1=tf.subtract(f0,field2)
   f2=tf.multiply(modulus1,tf.pow(f1,2))
   dmodulus=tf.multiply(modulus1,tf.pow(f1,2))
   dshear=tf.multiply(shear_modulus1,tf.pow(f1,2))
   with tf.GradientTape(persistent=True) as t2 :
     with tf.GradientTape(persistent=True) as t1 :
      t1.watch(x11)
      t1.watch(y11)
      t2.watch(x11)
      t2.watch(y11)
      ux,uy=model1(inputs=[sigma1,x11,y11,f2,load1,boundary1])
      stressy=tf.multiply(dmodulus,t1.gradient(uy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO))
      stressx=tf.multiply(dmodulus,t1.gradient(ux, x11,unconnected_gradients=tf.UnconnectedGradients.ZERO))  
      stressxy=tf.multiply(dshear,tf.add(t1.gradient(ux,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO),t1.gradient(uy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)))
   stressxx=t2.gradient(stressx,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressyy=t2.gradient(stressy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressxyx=t2.gradient(stressxy,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressxyy=t2.gradient(stressxy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
   stressx=tf.reshape(stressx,shape=(x11.shape[0],1))
   stressy=tf.reshape(stressy,shape=(x11.shape[0],1))
   stressxy=tf.reshape(stressxy,shape=(x11.shape[0],1)) 
   sigma_pred=tf.stack([stressx,stressy,stressxy],1)
   sigma_pred=tf.reshape(sigma_pred,shape=(x11.shape[0],3))
   H=Hcalculator(stressx,stressy,stressxy,c2,friction1)
   return stressxx,stressyy,stressxyx,stressxyy,sigma_pred,H

def gradient(x11,y11,H,field2,input4,input5) :

 with tf.GradientTape(persistent=True) as t3 :
      with tf.GradientTape(persistent=True) as t4 :
         t3.watch(x11)
         t3.watch(y11)
         t4.watch(x11)
         t4.watch(y11)
         field_predict=model2(inputs=[x11,y11,H,field2,input4,input5])
      fix=t4.gradient(field_predict,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
      fiy=t4.gradient(field_predict,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
 fixx=t3.gradient(fix,x11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
 fiyy=t3.gradient(fiy,y11,unconnected_gradients=tf.UnconnectedGradients.ZERO)
 return fixx,fiyy

def Hcalculator(stressx,stressy,stressxy,c3,friction3,H):
    
    sigma11,sigma33=eigen(stressx,stressy,stressxy)
    wc1=tf.divide(tf.subtract(sigma11,sigma33),tf.math.cos(friction3))
    wc2=tf.multiply(tf.add(sigma11,sigma33),tf.math.tan(friction3))
    wc3=tf.subtract(tf.add(wc1,wc2),c3)
    wc4=tf.math.maximum(wc3,tf.constant(0,dtype=tf.float32)) 
    wc=tf.math.square(wc4)
    H1=H
    H=wc
    H3=np.zeros((wc.shape[0],1))
    for i in range(0,wc.shape[0]) :
      H2=tf.cond(H1[i].numpy()>H[i].numpy(),lambda:wc[i].numpy(),lambda:wc[i].numpy())
      H3[i]=H2
    H3=tf.convert_to_tensor(H3,dtype=tf.float32)  
    return H

cordx=tf.keras.layers.Input(shape=(1,))
cordy=tf.keras.layers.Input(shape=(1,))
H=tf.keras.layers.Input(shape=(1,))
field2=tf.keras.layers.Input(shape=(1,))
input4=tf.keras.layers.Input(shape=(1,))
input5=tf.keras.layers.Input(shape=(1,))

x0=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordx)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)
x0=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x0)
x0=tf.keras.layers.BatchNormalization()(x0)

y1=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordy)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)
y1=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(y1)
y1=tf.keras.layers.BatchNormalization()(y1)

x1=tf.keras.layers.Multiply()([x0,y1])

x2=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(H)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)
x2=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x2)
x2=tf.keras.layers.BatchNormalization()(x2)

x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(field2)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)

x4=tf.keras.layers.Multiply()([input4,x1])
x4=tf.keras.layers.BatchNormalization()(x4)
x5=tf.keras.layers.Multiply()([x2,x1])
x5=tf.keras.layers.BatchNormalization()(x5)
x6=tf.keras.layers.Multiply()([input5,x1])
x6=tf.keras.layers.BatchNormalization()(x6)
x7=tf.keras.layers.Add()([tf.keras.layers.Add()([x4,x5]),x6])
x7=tf.keras.layers.BatchNormalization()(x7)
x8=tf.keras.layers.Multiply()([input5,x3])
x8=tf.keras.layers.BatchNormalization()(x8)
x9=tf.keras.layers.Subtract()([tf.keras.layers.Multiply()([x2,x3]),x2])
x9=tf.keras.layers.BatchNormalization()(x9)
x10=tf.keras.layers.Add()([tf.keras.layers.Add()([input4,x8]),x9])
x10=tf.keras.layers.BatchNormalization()(x10)
x11=tf.keras.layers.Multiply()([x10,x1])
x11=tf.keras.layers.BatchNormalization()(x11)
field_predict=tf.keras.layers.Multiply()([x7,x11])

model2 = Model(inputs=[cordx,cordy,H,field2,input4,input5], outputs=[field_predict])

sigma1=tf.keras.layers.Input(shape=(3,))
cordx=tf.keras.layers.Input(shape=(1,))
cordy=tf.keras.layers.Input(shape=(1,))
f2=tf.keras.layers.Input(shape=(1,))
load1=tf.keras.layers.Input(shape=(1,))
boundary1=tf.keras.layers.Input(shape=(1,))

a1=tf.keras.layers.Dense(3,activation='tanh',use_bias=True)(sigma1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)
a1=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(a1)
a1=tf.keras.layers.BatchNormalization()(a1)


x2x=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordx)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)
x2x=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x2x)
x2x=tf.keras.layers.BatchNormalization()(x2x)


x2y=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(cordy)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)
x2y=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x2y)
x2y=tf.keras.layers.BatchNormalization()(x2y)

x2=tf.keras.layers.Multiply()([x2x,x2y])  

x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(f2)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
x3=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x3)
x3=tf.keras.layers.BatchNormalization()(x3)
   
x4=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(load1)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(firstlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(secondlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(thirdlayer,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
x4=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x4)
x4=tf.keras.layers.BatchNormalization()(x4)
   
k=tf.keras.layers.Multiply()([x2,x3])
k=tf.keras.layers.BatchNormalization()(k)
fint=tf.keras.layers.Multiply()([a1,x2])
fint=tf.keras.layers.BatchNormalization()(fint)
fdelta=tf.keras.layers.Multiply()([tf.keras.layers.Multiply()([x4,x2]),x3])
fdelta=tf.keras.layers.BatchNormalization()(fdelta)
ftot=tf.keras.layers.Add()([fint,fdelta])
ftot=tf.keras.layers.BatchNormalization()(ftot)
x5=tf.keras.layers.Multiply()([k,ftot])
x5=tf.keras.layers.BatchNormalization()(x5)
x6=tf.keras.layers.Dense(fourthlayer,activation='tanh',use_bias=True)(x5)
x6=tf.keras.layers.BatchNormalization()(x6)
x7=tf.keras.layers.Dense(fourthlayer,activation='tanh',use_bias=True)(x5)
x7=tf.keras.layers.BatchNormalization()(x7)
x61=tf.keras.layers.Multiply()([x6,boundary1])
x61=tf.keras.layers.BatchNormalization()(x61)
ux=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x61)
x71=tf.keras.layers.Multiply()([x7,boundary1])
x71=tf.keras.layers.BatchNormalization()(x71)
uy=tf.keras.layers.Dense(1,activation='tanh',use_bias=True)(x71)


model1=Model(inputs=[sigma1,cordx,cordy,f2,load1,boundary1],outputs=[ux,uy])
