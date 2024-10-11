# waveboard
Repository for the control software of the waveboard

## Installation
add 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/user/Waveboard/lib' to your '.bashrc' file


## Ilarizzazione waveboard
*11 Ottobre 2024*

### 0) Verificare posizione jumperino blu "JP1"
[immagine]
- Va messo fra "max 5V" e "P 5 V 0"

![IMG_3094](https://github.com/user-attachments/assets/f9b675bf-208a-4742-ae5b-e637b82b7048)


### 1) Calibrazione in voltaggio
*"I canali mi stanno dando lo stesso voltaggio che io gli ho detto di dare via interfaccia?*
- Da un terminale collegato via ethernet alla WB si da
``` bash
ssh root@192.168.137.30
[inserire pwd]
./SetHV -c {n} -p 27.5 -v
```
- Così ho chiesto di settare il dato canale a 27.5V
- Il programma ti chiede di leggere due valori di voltaggio col multimetro e inserirli
![IMG_3092](https://github.com/user-attachments/assets/962a97b9-90ee-428f-8de3-50e9d24d2749)
- Alla fine della procedura il multimetro dovrebbe leggere 27.5V
	- Tuttavia, i vari valori di `m` e `q` per ogni canale vanno copiati nel file `config_ultra.py`, in modo che possano essere caricati all'apertura della GUI
	- Si assume quindi che la calibrazione rimanga costante (a meno di eventi maggiori) in caso di spegni/riaccendi
![IMG_3095](https://github.com/user-attachments/assets/7126365e-24b6-4fa9-afff-10b91157a4a4)
