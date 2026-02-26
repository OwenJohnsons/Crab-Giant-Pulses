import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scienceplots; plt.style.use(['science','no-latex'])


data = np.genfromtxt("JB_dms.txt", dtype=str)
dates = np.array(data[:, 0], dtype="datetime64[D]")
dm = data[:, 1].astype(float)

plt.figure(figsize=(9, 3))
plt.step(dates, dm, where="post",
         label="Jodrell Bank Ephemeris", color='k')

# plt.xlabel("Date")
plt.ylabel("DM [pc cm$^{-3}$]")

# Format ticks as Year-Month
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4)) 
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

plt.xticks(rotation=45, ha='right')
plt.xlim(dates[0], dates[-1])
plt.legend()

plt.tight_layout()
plt.savefig("DM_time.pdf")
plt.show()