# waveboard
Repository for the control software of the waveboard

## Installation
add 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/user/Waveboard/lib' to your '.bashrc' file


# Ilarizzazione waveboard
*11 Ottobre 2024*

### 0) Verificare posizione jumperino blu "JP1"
[immagine]
- Va messo fra "max 5V" e "P 5 V 0"

![IMG_3094](https://github.com/user-attachments/assets/f9b675bf-208a-4742-ae5b-e637b82b7048)


### 1) Calibrazione in voltaggio (~5min)
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


## 2) Calibrazione ADC-Volt (~1h)
- Generare un'onda "pulse" (durata 200ns, frequenza 100Hz) da 100, 200, 300, 400, 800 e 1000 mV, lavorando sempre con attenuatore in 0.1
![IMG_3096](https://github.com/user-attachments/assets/a93ba73a-cf32-4329-83b2-dac477935f90)

- Si manda questa onda nel segnale di un canale per volta, avendo disattivato l'HV, mettendo una soglia di entrata a 5mV
	- Per motivi pratici conviene su un singolo canale fare tutte le 6 onde quadre
- Per ogni configurazione (canale e voltaggio) si acquisiscono N forme d'onda
- [Update 04/03/2025] Si usa il comando plot nell'interfaccia grafica per verificare che i segnali siano quelli attesi, e contemporaneamente ciò converte i file in formato bin nei file in formato txt (quelli realmente analizzabili).
- Si passano poi queste forme d'onda (i file txt) al programma dedicato (`calwb3_x20.ipynb`) che identifica il plateau per fare la conversione ADC-V
	- Questo programma tira fuori per tutti i canali grafici e coefficienti angolari e intercetta sia Volt-ADC che ADC-Volt
- Questi numeri vanno messi a mano  nel file `config_ultra.py`

## 3) Calibrazione Dark Count (~3h)
*Tutti i canali (collegati ed alimentati) devono contare la stessa cosa in assenza di sorgente*
- Si collegano tutti i rivelatori, ma se ne alimentano metà per volta con soglia 1mV in entrata e 1mV in uscitas
- Senza sorgente, si lancia una acquisizione di ~1h di forme d'onda, creando un file `.bin`
- Questo file va passato dentro l'interfaccia grafica che lo converte in un file  `.txt` per ogni canale con dentro tutto l'elenco delle forme d'onda
- C'è un programma per generare tutti i timestamp di ogni singola forma d'onda
```bash
cd waveboard/bin
./HitViewer_arm -f file.bin -c {n channel} -t >> nome_file_n.txt
```
- Dai timestamp ottieni la rate (perché la WB scrive solo quando riceve qualcosa)
- Dal file `.txt` delle forme d'onda si fa la cumulativa (`nuova_scelta_soglia_buio.ipynb`), e da queste si vede quale soglia (in entrata) scegliere per arrivare ad una dark current di ~0.5CPS
- Ottenuta la soglia, la si imposta sulla GUI, e si fa la verifica con rate monitor
	- La differenza eventuale potrebbe essere dovuta al fatto che si sta impostando solo una delle soglie
- In teoria a questo punto tutti i canali hanno stessa DC, ma non per forza stessi conteggi su sorgente
## 4) Calibrazione su sorgente
*Adattare i Vbias per avere steso conteggio su sorgente*
- Si mettono a coppie i rivelatori sulla sorgente di Sr estesa e si prendono le rate
- Per ciascun canale si trova il Vbias che fa contare quanto il canale di riferimento
