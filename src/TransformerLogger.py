class TransformerLogger(object):
    
    matching_log_file = None
    error_log_file = None
    choice_log_file = None
    analytic_log_file = None

    def __init__(self):
        self.matching_log_file = 'C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/matching_log.txt'
        self.error_log_file = 'C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/error_log.txt'
        self.choice_log_file = 'C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/choice_log.txt'
        self.analytic_log_file = 'C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/analytic_log.txt'
        return
    
    def log_start(self):
        with open(self.matching_log_file,'w') as log:
            log.close()
        with open(self.error_log_file,'w') as log:
            log.close()
        with open(self.choice_log_file,'w') as log:
            log.close()
        with open(self.analytic_log_file,'w') as log:
            log.close()
        
    def add_matching_log(self,log_entry):
        with open(self.matching_log_file,'a+') as log:
            log.write(log_entry)
            log.write("\n")
            log.close()
    
    def add_matching_separation(self):
        with open(self.matching_log_file,'a+') as log:
            log.write("\n")
            log.write("=================================================================================================================================")
            log.write("\n")
            log.write("#################################################################################################################################")
            log.write("\n")
            log.write("=================================================================================================================================")
            log.write("\n")
            log.write("\n")
            log.close()
        
    def add_error_log(self,log_entry):
        with open(self.error_log_file,'a+') as log:
            log.write(log_entry)
            log.write("\n")
            log.close()
        
    def add_choice_log(self,log_entry):
        with open(self.choice_log_file,'a+') as log:
            log.write(log_entry)
            log.write("\n")
            log.close()
    
    def add_analytic_log(self,log_entry):
        with open(self.analytic_log_file,'a+') as log:
            log.write(log_entry)
            log.write("\n")
            log.close()
    