import matplotlib.pyplot as plt
import model_SIR as SIR
import numpy as np


# test dynamicsCT (called by gen_SIR_I) and gen_SIR_I

population = 100000
beta_test = 0.2
gamma_test = 1/20
print('accordingly, the reproductive number R_0 is {}'.format(beta_test/gamma_test))
I_initial = 15
t_end = 300

t = np.array(range(t_end+1))

y_sim = SIR.gen_SIR_I(t, beta_test, gamma_test, population, I_initial, R0=0)
#print(len(y_sim), len(t))


fig,ax = plt.subplots();
ax.plot(t,y_sim)
ax.set(xlabel='time (days)',ylabel='number of infected', 
	title='Simulation of a SIR model \n with ($\\beta$,$\\gamma$) = ({},{})/day'.format(beta_test, gamma_test))
ax.grid()
plt.show()
