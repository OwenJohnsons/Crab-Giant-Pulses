import psrchive
import numpy as np
import matplotlib.pyplot as plt
import scienceplots; plt.style.use(['science','no-latex'])

def _load_psrchive(fname, dm):
    """Load data from a PSRCHIVE file.

    Parameters
    ----------
    fname : str
        Archive (.ar) to load.

    Returns
    -------
    waterfall : array_like
        Burst dynamic spectrum.
    f_channels : array_like
        Center frequencies, in MHz.
    t_res : float
        Sampling time, in s.

    """
    archive = psrchive.Archive_load(fname)
    archive.pscrunch()
    # un-dedisperse
    archive.set_dispersion_measure(0.)
    archive.dedisperse()
    archive.set_dedispersed(False)
    # archive.centre() # no polyco
    
    archive.set_dispersion_measure(dm)
    archive.dedisperse()
    archive.set_dedispersed(True)
    archive.tscrunch()
    
    weights = archive.get_weights().squeeze()
    waterfall = np.ma.masked_array(archive.get_data().squeeze())
    waterfall[weights == 0] = np.ma.masked
    f_channels = np.array([
        archive.get_first_Integration().get_centre_frequency(i) \
        for i in range(archive.get_nchan())])
    t_res = archive.get_first_Integration().get_duration() \
        / archive.get_nbin()

    if archive.get_bandwidth() < 0:
        waterfall = np.flipud(waterfall)
        f_channels = f_channels[::-1]

    return waterfall, f_channels, t_res



def main():
    
    uc_waterfall, uc_f_channels, uc_t_res = _load_psrchive('Crab_uncorrected.ar', dm=56.8)
    c_waterfall, c_f_channels, c_t_res = _load_psrchive('Crab_uncorrected.ar', dm=56.711)
    print("Waterfall shape:", uc_waterfall.shape)
    
    # uc_t_res
    
    # mask time from 0.12 to 0.17 
    time_mask = (np.arange(uc_waterfall.shape[1]) * uc_t_res >= 0.1) & (np.arange(uc_waterfall.shape[1]) * uc_t_res <= 0.21)
    # invert mask to keep only time from 0.12 to 0.17
    uc_waterfall = uc_waterfall[:, time_mask]
    c_waterfall  = c_waterfall[:, time_mask]
    print("Masked waterfall shape:", uc_waterfall.shape)
    
    freq = np.linspace(uc_f_channels.min(), uc_f_channels.max(), uc_waterfall.shape[1])
    uc_avg_spectrum = np.mean(uc_waterfall, axis=0)
    c_avg_spectrum = np.mean(c_waterfall, axis=0)
   
    # gridspec 2x2, share x axis 
    
    fig, axs = plt.subplots(
        2, 2,
        figsize=(6, 9),
        sharex=False,
        sharey='row', 
        gridspec_kw={'height_ratios': [1, 6], 'hspace': 0}
    )
    
    # ---- Top row: spectra ----
    axs[0, 0].plot(freq, uc_avg_spectrum/np.max(c_avg_spectrum), color='black')
    axs[0, 1].plot(freq, c_avg_spectrum/np.max(c_avg_spectrum), color='black')
    # add text for SNR and DM values 
    axs[0, 0].text(0.79, 0.85, "DM = 56.8", transform=axs[0, 0].transAxes, ha='center', va='center')
    axs[0, 0].text(0.8, 0.73, "SNR = 762.9", transform=axs[0, 0].transAxes, ha='center', va='center')
        
    axs[0, 1].text(0.79, 0.85, "DM = 56.711", transform=axs[0, 1].transAxes, ha='center', va='center')
    axs[0, 1].text(0.8, 0.73, "SNR = 1839.1", transform=axs[0, 1].transAxes, ha='center', va='center')
    
    # x-limits
    axs[0, 0].set_xlim(freq.min(), freq.max())
    axs[0, 1].set_xlim(freq.min(), freq.max())

    # Remove x ticks on top row
    for ax in axs[0, :]:
        ax.tick_params(labelbottom=False, bottom=False)

    # ---- Bottom row: waterfalls ----
    im0 = axs[1, 0].imshow(
        uc_waterfall,
        cmap='Greens',
        aspect='auto',
        origin='lower',
        extent=[0, uc_waterfall.shape[1]*uc_t_res,
                uc_f_channels.min(), uc_f_channels.max()]
    )

    im1 = axs[1, 1].imshow(
        c_waterfall,
        cmap = 'Greens',
        aspect='auto',
        origin='lower',
        extent=[0, c_waterfall.shape[1]*c_t_res,
                c_f_channels.min(), c_f_channels.max()]
    )

    # ---- Only left column keeps y ticks ----
    for ax in axs[:, 1]:
        ax.tick_params(labelleft=False)
        ax.set_ylabel("")

    # Labels
    axs[1, 0].set_xlabel("Time (s)")
    axs[1, 1].set_xlabel("Time (s)")
    axs[1, 0].set_ylabel("Frequency (MHz)")
    plt.tight_layout()
    plt.savefig('DMcompare.png', dpi=300)
    plt.savefig('DMcompare.pdf', dpi=300)
  
if __name__ == "__main__":
    main()