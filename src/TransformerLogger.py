class TransformerLogger(object):
    
    matching_log_file = None
    error_log_file = None
    choice_log_file = None

    def __init__(self):
        return
    
    def log_start(self):
        self.matching_log_file = open('C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/matching_log.txt', 'w')
        self.error_log_file = open('C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/error_log.txt', 'w')
        self.choice_log_file = open('C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/choice_log.txt', 'w')
        
    def add_matching_log(self,log_entry):
        self.matching_log_file.write(log_entry)
        self.matching_log_file.write("\n")
        
    def add_error_log(self,log_entry):
        self.error_log_file.write(log_entry)
        self.error_log_file.write("\n")
        
    def add_choice_log(self,log_entry):
        self.choice_log_file.write(log_entry)
        self.choice_log_file.write("\n")
    
    def log_exit(self):
        self.matching_log_file.close()
        self.error_log_file.close()
        self.choice_log_file.close()