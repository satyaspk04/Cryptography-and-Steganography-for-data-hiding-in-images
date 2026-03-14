# Cryptography-and-Steganography-for-data-hiding-in-images
📌 Project Overview
This project presents a novel dual-layered security architecture that combines Cryptography and Steganography to ensure high-level data confidentiality and integrity. By encrypting sensitive information and subsequently embedding it within a digital image, we eliminate the "suspicion of communication," making the data both unreadable and invisible to unauthorized parties.

This implementation is based on my research paper published in IEEE Xplore: Cryptography and Steganography for Data Hiding in Images: A Novel Architecture and Implementation.

🚀 Key Features
Dual-Layer Security: Combines robust cryptographic algorithms for data scrambling with steganographic techniques for data hiding.

High Payload Capacity: Optimized embedding logic to maximize the amount of data hidden without degrading the cover image quality.

Visual Integrity: Ensures a high Peak Signal-to-Noise Ratio (PSNR) so that the stego-image remains indistinguishable from the original.

Secure Extraction: Proprietary extraction logic that requires specific keys to retrieve and decrypt the hidden payload.

🛠 Tech Stack
Language: **Python**

Libraries:  **Flask** , Pillow , NumPy , zlib , PyCryptodome , uuid , Requests.

Concepts: Least Significant Bit (LSB) Encoding, AES 256 Encryption, Image Processing.

📖 Architecture
Encryption Phase: The plaintext message is transformed into ciphertext using a cryptographic key.

Embedding Phase: The ciphertext is embedded into the pixels of a cover image using a novel steganographic algorithm.

Transmission: The stego-image is shared through standard digital channels.

Extraction & Decryption: The receiver extracts the ciphertext from the image and decrypts it back to the original message.

📊 Results and Metrics
As detailed in the IEEE publication, the system achieved:

High PSNR Values: Minimal distortion in stego-images.

Robustness: Resistance against common image manipulation attacks.

Efficiency: Low computational overhead suitable for real-time applications.
