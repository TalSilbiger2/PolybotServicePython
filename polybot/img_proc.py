from pathlib import Path
from matplotlib.image import imread, imsave
import random
from loguru import logger


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path


    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result


    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j-1] - row[j]))

            self.data[i] = res


    def rotate(self):
        # Check if the image is non-empty
        if not self.data or not all(self.data):
            raise RuntimeError("Invalid image format. Image cannot be empty.")

        # Transpose and reverse rows to rotate 90 degrees clockwise
        rotated_image = [[self.data[row][col] for row in range(len(self.data) - 1, -1, -1)]
                         for col in range(len(self.data[0]))]

        # Store the rotated image in self.data
        self.data = rotated_image

    def salt_n_pepper(self, salt_prob=0.2, pepper_prob=0.2):
        total_pixels = len(self.data) * len(self.data[0])
        num_salt = int(salt_prob * total_pixels)
        num_pepper = int(pepper_prob * total_pixels)

        # Flatten the image data for easier manipulation
        flat_image = [pixel for row in self.data for pixel in row]

        # Generate unique indices for salt and pepper
        all_indices = list(range(total_pixels))
        salt_indices = set(random.sample(all_indices, num_salt))
        pepper_indices = set(random.sample(all_indices, num_pepper))

        # Ensure salt and pepper indices do not overlap
        while salt_indices & pepper_indices:
            overlap = salt_indices & pepper_indices
            pepper_indices -= overlap
            remaining_indices = list(set(all_indices) - salt_indices - pepper_indices)
            pepper_indices.update(random.sample(remaining_indices, len(overlap)))

        # Apply salt noise
        for idx in salt_indices:
            flat_image[idx] = (255, 255, 255)  # White pixel (salt)

        # Apply pepper noise
        for idx in pepper_indices:
            flat_image[idx] = (0, 0, 0)  # Black pixel (pepper)

        # Reshape flat image back into the original structure
        self.data = [flat_image[i:i + len(self.data[0])] for i in range(0, total_pixels, len(self.data[0]))]

    def concat(self, other_img, direction='horizontal'):

        concatenated_image = []

        # Ensure both images have the same height
        if direction == 'horizontal':
            if len(self.data) != len(other_img.data):
                raise RuntimeError("Images must have the same height for horizontal concatenation.")
            else:
                # Iterate over each row and concatenate horizontally
                for row1, row2 in zip(self.data, other_img.data):
                    # Combine the rows side-by-side
                    concatenated_row = row1 + row2
                    # Initialize an empty list to store the concatenated image data
                    concatenated_image.append(concatenated_row)  # 1 list together


        elif direction == 'vertical':
            if any(len(row) != len(other_img[0]) for row in self.data) or any(
                    len(row) != len(self.data[0]) for row in other_img):
                raise RuntimeError("Images must have the same width for vertical concatenation.")
            else:
                concatenated_image = self.data + other_img
            # Iterate over each row and concatenate horizontally
            for row in other_img.data:
                # Combine the rows at image end
                self.data.append(row)
        else:
            raise ValueError("Invalid direction. Use 'horizontal' or 'vertical'.")

        # Store the result in self.data
        self.data = concatenated_image


    def segment(self):
        # Intensity Calculation: For each pixel, we calculate the intensity by averaging its RGB values.
        # Create a new list to store the segmented image
        segmented_image = []

        for row in self.data:
            segmented_row = []
            for pixel in row:
                intensity = sum(pixel)/3
                if intensity > 100:
                    segmented_row.append((255,255,255)) # white pixel
                else:
                    segmented_row.append((0, 0, 0)) # black pixel

            segmented_image.append(segmented_row)

        logger.info("The Image is:")
        self.data = segmented_image
