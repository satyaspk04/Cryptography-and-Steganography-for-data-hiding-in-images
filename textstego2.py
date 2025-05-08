import zlib
from PIL import Image
import numpy as np
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

class TextSteganography:
    def __init__(self, key_size=32):
        """Initialize with a random encryption key."""
        self.key = get_random_bytes(key_size)
        
    def compress_text(self, text):
        """Compress text using zlib."""
        return zlib.compress(text.encode())
    
    def decompress_text(self, compressed_data):
        """Decompress zlib compressed data."""
        return zlib.decompress(compressed_data).decode()
    
    def encrypt(self, data):
        """Encrypt data using AES-256 in CBC mode."""
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return f"{iv}:{ct}"
    
    def decrypt(self, encrypted_data):
        """Decrypt AES-256 encrypted data."""
        try:
            iv, ct = encrypted_data.split(':')
            iv = base64.b64decode(iv)
            ct = base64.b64decode(ct)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return unpad(cipher.decrypt(ct), AES.block_size)
        except ValueError as e:
            raise ValueError("Failed to decrypt data. The image may be corrupted.") from e
    
    def prepare_image(self, image_path):
        """Prepare image for steganography by converting to RGB."""
        try:
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            return img
        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}") from e
    
    def get_embedding_capacity(self, img):
        """Calculate how many bits can be stored in the image."""
        width, height = img.size
        return (width * height * 3) - 32  # Subtract 32 bits reserved for length
    
    def get_pixel_position(self, pos, width, height):
        """Calculate row, col, and channel from position."""
        total_pixels = width * height
        pixels_pos = pos // 3
        channel = pos % 3
        
        row = pixels_pos // width
        col = pixels_pos % width
        
        if row >= height:
            raise ValueError("Data too large for image dimensions")
            
        return row, col, channel
    
    def embed_data(self, image_path, text, output_path):
        """Embed compressed and encrypted text into image using RGB channels."""
        try:
            # Prepare the data
            compressed_data = self.compress_text(text)
            encrypted_data = self.encrypt(compressed_data)
            data_bits = []
            
            # Convert encrypted data to bits
            for byte in encrypted_data.encode():
                data_bits.extend([int(bit) for bit in format(byte, '08b')])
            
            # Prepare the image
            img = self.prepare_image(image_path)
            width, height = img.size
            pixels = np.array(img)
            
            # Check capacity
            max_bits = self.get_embedding_capacity(img)
            if len(data_bits) > max_bits:
                raise ValueError(
                    f"Data too large. Image can store {max_bits//8} bytes, "
                    f"but data is {len(data_bits)//8} bytes"
                )
            
            # Create a copy of the pixel array
            modified_pixels = pixels.copy()
            
            # Embed length (32 bits)
            length_bits = format(len(data_bits), '032b')
            pos = 0
            
            for i in range(32):
                row, col, channel = self.get_pixel_position(pos, width, height)
                pixel = int(modified_pixels[row, col, channel])
                modified_pixels[row, col, channel] = (pixel & 0xFE) | int(length_bits[i])
                pos += 1
            
            # Embed data
            for bit in data_bits:
                row, col, channel = self.get_pixel_position(pos, width, height)
                pixel = int(modified_pixels[row, col, channel])
                modified_pixels[row, col, channel] = (pixel & 0xFE) | bit
                pos += 1
            
            # Save with minimal compression
            Image.fromarray(modified_pixels).save(
                output_path, 
                format='PNG',
                optimize=True,
                compress_level=7
            )
            
        except Exception as e:
            raise ValueError(f"Failed to embed data: {str(e)}") from e
    
    def extract_data(self, image_path):
        """Extract and decrypt hidden text from image using RGB channels."""
        try:
            # Read and prepare the image
            img = self.prepare_image(image_path)
            width, height = img.size
            pixels = np.array(img)
            
            # Extract length (32 bits)
            length_bits = []
            pos = 0
            
            for i in range(32):
                row, col, channel = self.get_pixel_position(pos, width, height)
                length_bits.append(str(pixels[row, col, channel] & 1))
                pos += 1
            
            data_length = int(''.join(length_bits), 2)
            
            # Validate length
            max_bits = self.get_embedding_capacity(img)
            if data_length > max_bits:
                raise ValueError("Invalid data length detected. Image may be corrupted.")
            
            # Extract data bits
            extracted_bits = []
            for i in range(data_length):
                row, col, channel = self.get_pixel_position(pos, width, height)
                extracted_bits.append(pixels[row, col, channel] & 1)
                pos += 1
            
            # Convert bits to bytes
            extracted_bytes = bytes(
                int(''.join(map(str, extracted_bits[i:i+8])), 2)
                for i in range(0, len(extracted_bits), 8)
            )
            
            # Decrypt and decompress
            encrypted_data = extracted_bytes.decode()
            decrypted_data = self.decrypt(encrypted_data)
            original_text = self.decompress_text(decrypted_data)
            
            return original_text
            
        except Exception as e:
            raise ValueError(f"Failed to extract data: {str(e)}") from e

def main():
    stego = TextSteganography()
    input_text = "This is a secret message that will be compressed, encrypted, and hidden in the image!"
    input_image = "input.png"
    output_image = "output.png"
    
    try:
        # Test image capacity first
        img = Image.open(input_image)
        if img.mode != 'RGB':
            print(f"Converting image from {img.mode} to RGB mode...")
            
        capacity = stego.get_embedding_capacity(img) // 8
        print(f"Image can store approximately {capacity} bytes of data")
        
        # Proceed with embedding
        stego.embed_data(input_image, input_text, output_image)
        print("Text successfully hidden in image!")
        
        # Extract and verify
        extracted_text = stego.extract_data(output_image)
        print("\nExtracted text:", extracted_text)
        
        if extracted_text == input_text:
            print("\nSuccess! The extracted text matches the original.")
        else:
            print("\nWarning: The extracted text doesn't match the original.")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()