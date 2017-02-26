import os

def chiffrementCesar(motAChiffre,cle):
	motChiffre = []
	for lettre in motAChiffre:
		#print(ord(lettre))
		chiffre = ord(lettre)-97
		chiffre = (chiffre+cle)%26
		lettreChiffre = chr(chiffre+97)
		motChiffre.append(lettreChiffre)
	motChiffre = "".join(motChiffre)
	return motChiffre

def dechiffrementCesar(motChiffre,cle):
	motDechiffre = []
	for lettreChiffre in motChiffre:
		chiffre = ord(lettreChiffre)-97
		chiffre = (chiffre-cle)%26
		lettre = chr(chiffre+97)
		motDechiffre.append(lettre)
	motDechiffre = "".join(motDechiffre)
	return motDechiffre

chaine="salut"
chaineChiffre = chiffrementCesar(chaine,3)
chaineDechiffre = dechiffrementCesar(chaineChiffre,3)
print(chaineChiffre)
print(chaineDechiffre)

##

# ne fonctionne pas avec les espaces
# securite trop faible --> envisager chiffrement vigenere
# etudier repartition cles

##