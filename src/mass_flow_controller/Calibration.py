class calibration:
    def __init__(self,
                 input_val = None,
                 output_val = None,
                 cal_file = None,
                 units = None,
                 cal_type = 'Linear'):
        if (input_val is None) and (output_val==None) and (cal_file is None) and (units is None):
            try:
                self.read('cal_default.txt')
            # If the default calibration file doesn't exist it creates it.
            except:
                print('Creating default calibration file.')
                self.calibration(input_val = [0, 100],
                              output_val = [0.2, 5],
                              cal_file = 'cal_default.txt',
                              units = '%',
                              cal_type = cal_type)
        else:
            self.calibration(input_val = input_val,
                      output_val = output_val,
                      cal_file = cal_file,
                      units = units,
                      cal_type = cal_type)


    def calibration(self,
                  input_val = None,
                  output_val = None,
                  units = None,
                  cal_file = None,
                  cal_type = 'Linear'):
        check = [(input_val is None) and (output_val is None), cal_file is None]
        if check[0] and check[1]:
            # Return current calibration data
            print(self.read(self.filename))
            return
        if check[0] and not check[1]:
            # Read specified calibration file
            self.read(cal_file)
            return
        if not check[0]:
            # Calibrate the system
            results = {}
            results['units'] = units
            results['type'] = cal_type
            results['data: flowrate'] = input_val
            results['data: voltage'] = output_val
            # No calibration type besides Linear exists at this time.
            if cal_type is 'Linear':
                offset, scale = self.linear_calibration(output_val = output_val, 
                                                        input_val = input_val)
                results['offset'] = offset
                results['scale'] = scale
                self.offset = offset
                self.scale = scale
            self.units = units
            self.cal_type = cal_type
            if cal_file != None:
                self.write(results, cal_file)
                print('Calibration complete! Results saved to "{}"\n{}'.format(cal_file, results))
            else:
                print('Calibration complete! Results were not saved.\n{}'.format(results))
            return

    # Perform a regression on a set of inputs to obtain the offset and scale parameters.
    # The linear regression is written out explicitly to save space vs importing a library.
    def linear_calibration(self, output_val, input_val):
        count = len(input_val)
        if count != len(output_val):
            print('Inputs must be the same size!')
            return
        if count==2:
            scale = (output_val[1] - output_val[0])/(input_val[1] - input_val[0])
            offset = output_val[0] - scale*input_val[0]
            return offset, scale
        sum_y = sum(output_val)
        sum_x = sum(input_val)
        sum_x2 = sum([i**2 for i in input_val])
        sum_xy = sum([i*j for i,j in zip(input_val, output_val)])
        _delta = count*sum_x2 - sum_x**2
        scale = (count*sum_xy - sum_x*sum_y)/_delta
        offset = (sum_y*sum_x2 - sum_x*sum_xy)/_delta
        return offset, scale


    def write(self, results, filename):
        results['filename'] = filename
        txt = ''
        keys = sorted(results)
        for i in keys:
            txt += '{}: {}\n'.format(i, results[i])
        with open(filename, 'w') as f:
            f.write(txt)

    def read(self, filename):
        data = open(filename).read()
        keys = ['units', 'filename']
        cal_type = self.find(data, 'type')
        if cal_type is 'Linear':
            keys += 'offset', 'scale'
            results = {}
            for i in keys:
                results[i] = self.find(data, i)
            self.offset = results['offset']
            self.scale = results['scale']
        self.units = results['units']
        self.filename = results['filename']
        self.cal_type = cal_type
        return results


    def find(self, data, field):
        idx = data.find(field)
        rng = [data[idx:].find(':') + idx,
                 data[idx:].find('\n') + idx]
        value = data[rng[0]+2:rng[1]]
        try:
            result = float(data[rng[0]+2:rng[1]])
        except:
            result = data[rng[0]+2:rng[1]]
        return result

    # return y from y = mx + b (x is provided)
    def convert(self, x):
        if self.cal_type is 'Linear':
            y = x*self.scale + self.offset
            return y

    # Return x from y = mx + b (y is provided)
    def invert(self, y):
        if self.cal_type is 'Linear':
            x = (y - self.offset)/self.scale
            return x
