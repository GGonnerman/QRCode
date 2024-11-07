from itertools import zip_longest

def generate_log_antilog_table():
    generator_polynomial = 0b100011101
    from_power = {}
    for i in range(255):
        if i < 8:
            from_power[i] = 2**i
        else:
            current = from_power[i - 1] * 2
            if current >= 256:
                current ^= generator_polynomial
            from_power[i] = current

    to_power = {}
    for k, v in from_power.items():
        to_power[v] = k

    return (from_power, to_power)

class GFValue():

    a_power: int
    x_power: int
    view_as_int: bool = True

    def from_a_value(a_value: int, x_power: int):
        from_power, to_power = generate_log_antilog_table()
        return GFValue(to_power[a_value], x_power)

    def __init__(self, a_power: int, x_power: int):
        self.a_power = a_power
        self.x_power = x_power

    def __mul__(self, other):
        if not isinstance(other, GFValue):
            try:
                return other * self
            except:
                pass
            raise Exception("Cannot multiply a GFValue and a non-GFValue")
        return GFValue((self.a_power + other.a_power)%255, self.x_power + other.x_power)

    def __add__(self, other):
        if not isinstance(other, GFValue):
            try:
                return other + self
            except:
                pass
            raise Exception("Cannot multiply a GFValue and a non-GFValue")
        if self.x_power != other.x_power:
            raise Exception("Cannot add GFValues with different x exponents")
        from_power, to_power = generate_log_antilog_table()
        sap = from_power[self.a_power]
        oap = from_power[other.a_power]

        #print(self.a_power, other.a_power)
        new_value = sap ^ oap
        #print(new_value)
        new_a_power = to_power[new_value]
        #print(new_a_power)
        return GFValue(new_a_power, self.x_power)

    def __str__(self):
        if GFValue.view_as_int:
            from_power, to_power = generate_log_antilog_table()
            return f"{from_power[self.a_power]}x^({self.x_power})"
        else:
            return f"a^({self.a_power})*x^({self.x_power})"

    def __repr__(self):
        if GFValue.view_as_int:
            from_power, to_power = generate_log_antilog_table()
            return  f"<GFValue a_int={from_power[self.a_power]} x_power={self.x_power}"
        else:
            return  f"<GFValue a_power={self.a_power} x_power={self.x_power}"

class GFPolynomial():

    values: list

    def __init__(self, *gfValues):
        self.values = [v for v in gfValues]
        #print([str(v) for v in self.values])
        self.combine_like_terms()
        self.values.sort(key=lambda x: -x.x_power)

    def __add__(self, other):
        if(isinstance(other, GFPolynomial)):
            return GFPolynomial(*self.values, *other.values)
        elif(isinstance(other, GFValue)):
            return GFPolynomial(*self.values, other)
        else:
            raise ValueError(f"Cannot add GFPolynomial by {other.__class__.__name__}")

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, i):
        return self.values[i]

    def __mul__(self, other):
        if(isinstance(other, GFPolynomial)):
            new_values = []
            for a in self:
                for b in other:
                    new_values.append(a * b)
            return GFPolynomial(*new_values)
        elif(isinstance(other, GFValue)):
            return GFPolynomial(*[v*other for v in self])
        else:
            raise ValueError(f"Cannot multiply GFPolynomial by {other.__class__.__name__}")

    def combine_like_terms(self):
        self.values.sort(key=lambda v: -v.x_power)
        i = 0
        while i < len(self.values) - 1:
            a = self.values[i]
            b = self.values[i + 1]
            if a.x_power == b.x_power:
                self.values[i] = a + b
                self.values.pop(i + 1)
                continue
            i += 1

    def __str__(self):
        return " + ".join([str(x) for x in self])

    def __len__(self):
        return max([v.x_power for v in self])

    # TODO: This assume we have same x power on all terms and same num of term, which is probably not a good assumption
    def __xor__(self, other):
        if not isinstance(other, GFPolynomial):
            try:
                other ^ self
            except:
                pass
            raise ValueError(f"Cannot xor GFPolynomial by {other.__class__.__name__}")
        new_values = []
        from_power, to_power = generate_log_antilog_table()
        for a, b in zip_longest(self, other, fillvalue=None):
            # Ensure that a is the existing value
            if a is None and b is not None:
                a = b
                b = None

            if b is None:
                new_value = from_power[a.a_power] ^ 0
            else:
                new_value = from_power[a.a_power] ^ from_power[b.a_power]

            if new_value == 0: continue

            new_values.append(GFValue.from_a_value(new_value, a.x_power))
        return GFPolynomial(*new_values)

    def as_integers(self):
        from_power, to_power = generate_log_antilog_table()
        out = [0 for i in range(len(self)+1)]
        for v in self:
            out[v.x_power] = from_power[v.a_power]
        out.reverse()
        return out


def generate_ec_codeword_polynomial(codeword_count):
    polynomial = GFPolynomial(GFValue(0, 1), GFValue(0, 0))
    for i in range(1, codeword_count):
        polynomial *= GFPolynomial(GFValue(0, 1), GFValue(i, 0))
    return polynomial

def generate_message_polynomial(message: list):
    coeff = [int(w, 2) for w in message]
    coeff.reverse()
    polynomial = GFPolynomial()
    for i, val in enumerate(coeff):
        polynomial += GFValue.from_a_value(val, i)
    return polynomial

def perform_long_division(message_polynomial, codeword_count):
    generator_polynomial = generate_ec_codeword_polynomial(codeword_count)

    original_message_polynomial_size = len(message_polynomial) + 1 # Plus one because we use x^0

    # Multiply by n^x to make sure the message polynomial doesn't get too small
    message_polynomial *= GFValue(0, codeword_count)

    for i in range(original_message_polynomial_size):
        # Multiply the generator polynomial so the lead term hsa the same power as the lead term of message polynomial
        current_generator_polynomial = generator_polynomial * GFValue(0, len(message_polynomial) - len(generator_polynomial))

        # Multiply the generator polynomial so it has the same first term
        current_generator_polynomial *= GFValue(message_polynomial[0].a_power - generator_polynomial[0].a_power, 0)

        GFValue.view_as_int = True

        message_polynomial ^= current_generator_polynomial

    print(message_polynomial)

    return message_polynomial
        #print(message_polynomial)
        #print()
        #print(generator_polynomial)
        #print()
        #print(generator_polynomial[0])

#mp = generate_message_polynomial("00100000 01011011 00001011 01111000 11010001 01110010 11011100 01001101 01000011 01000000 11101100 00010001 11101100 00010001 11101100 00010001".split(" "))

#print(perform_long_division(mp, 10).as_integers())
#mp = 
#print(perform_long_division(message_polynomial, codeword_count))
#print(generate_ec_codeword_polynomial(10))
#lj = l * j
#k = GFPolynomial(GFValue(0, 1), GFValue(2, 0))
#ljk = lj * k
#print()
#print(ljk)
#gfp = GFPolynomial(l, j)

#a = [ 0, 0 ]
#b = [ 1, 0 ]
#o = [ 0, 0, 0 ]
#
#for ax, aa in enumerate(a):
#    for bx, ba in enumerate(b):
#        print(f"a^({aa}) x^({ax}) mult a^({ba}) x^({bx})")
#
#print(o)

# 2 = (a^0 x - a^0) * (a^0 x - a^1)
# 3 = (a^0 x - a^0) * (a^0 x - a^1) * (a^0 x - a^2)
# 4 = (a^0 x - a^0) * (a^0 x - a^1) * (a^0 x - a^2) * (a^0 x - a^3)

# 2 = (1 x - 1) * (1 x - a^1)
# 3 = (1 x - 1) * (1 x - a^1) * (1 x - a^2)
# 4 = (1 x - 1) * (1 x - a^1) * (1 x - a^2) * (1 x - a^3)
#start = [
