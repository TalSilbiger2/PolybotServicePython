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

    def salt_n_pepper(self):
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                rand_num = random.random()

                if rand_num < 0.2:
                    self.data[i][j] = 255

                elif rand_num > 0.8:
                    self.data[i][j] = 0

        self.save_img()

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
                # Ensure pixel is a tuple or list with 3 components
                if isinstance(pixel, (list, tuple)) and len(pixel) == 3:
                    intensity = sum(pixel) / 3
                else:
                    raise ValueError(f"Invalid pixel format: {pixel}. Expected a tuple or list of length 3.")

                if intensity > 100:
                    segmented_row.append((255, 255, 255))  # White pixel
                else:
                    segmented_row.append((0, 0, 0))  # Black pixel

            segmented_image.append(segmented_row)

        # Log the segmentation process
        logger.info("Image segmentation complete.")

        # Update the image data
        self.data = segmented_image
