# srsRAN Docker Container setup

Docker appears to be set up to build several services:
* a open5GS 5gc container 
* a srsRAN gnb 
* a metrics server (not sure what the role of this is yet)
* influxdb (some sort of db, but not quite sure what this does)
* grafana (not sure what this is, but putting it here for completeness)

### gnb yml configuration for COTS UE
There appears to be several yml configurations for the gnb within the srsran project.
They are listed below for convienience. There is not one spesific to the sdr that
we will be using (N210), but one can probably be copied and modified to work.
* `srsRAN_Project/configs/gnb_rf_b210_fdd_srsUE.yml`
* `srsRAN_Project/configs/gnb_rf_n310_fdd_n3_20mhz.yml`
* `srsRAN_Project/configs/du_rf_b200_tdd_n78_20mhz.yml`
* `srsRAN_Project/configs/gnb_custom_cell_properties.yml`
* `srsRAN_Project/configs/gnb_rf_b200_tdd_n78_20mhz.yml`

### Open5GS yml configuration for COTS UE
The open5GS container takes a file called `open5gs-5gc.yml` that lives in the location:
`srsRAN_Project/docker/open5gs/open5gs-5gc.yml`. The open5GS setup in the
[srsRAN with COTS UE](https://docs.srsran.com/projects/project/en/latest/tutorials/source/cotsUE/source/index.html)
tutorial shows a few lines modified in some yml files (`amf.yml` and `upf.yml`), so this appears
to be where they would be if we wanted to change them.
Not sure as of now what is required to be changed.


