import re


class Columnizer():
    COLUMN_LIST = None
    WIDTH = 20

    def __init__(self, width=20):
        self.WIDTH = width
        self.COLUMN_LIST = []

    def add_column(self, column):
        if type(column) != list:
            raise ValueError
        new_column = []
        for i in column:
            x = pad(i, self.WIDTH)
            new_column += [x]
        self.COLUMN_LIST += [new_column]

    def __str__(self):
        longest = 0
        return_string = ""
        for i in self.COLUMN_LIST:
            if len(i) > longest:
                longest = len(i)

        # Print start
        return_string += "┌"
        for i in range(0, len(self.COLUMN_LIST)):
            return_string += "─" * self.WIDTH
            if i == len(self.COLUMN_LIST) - 1:
                return_string += "┐\n"
            else:
                return_string += "┬"

        # Print body
        for i in range(0, longest):
            for j in self.COLUMN_LIST:
                return_string += "│"
                try:
                    return_string += j[i]
                except(IndexError):
                    return_string += " " * self.WIDTH
            return_string += "│\n"

        # Print end
        return_string += "└"
        for i in range(0, len(self.COLUMN_LIST)):
            return_string += "─" * self.WIDTH
            if i == len(self.COLUMN_LIST) - 1:
                return_string += "┘"
            else:
                return_string += "┴"
        return return_string


def pad(text, width):
    regex = re.compile("\033.*?m")
    length = len(regex.sub("", str(text)))
    padding = width - length
    if padding > 0:
        text = " " * (padding//2) + str(text) + " " * ((padding+1)//2)
    return text
