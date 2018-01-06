from HTMLParser import HTMLParser
import petadmin


# create a subclass and override the handler methods
class BookingRequestHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.phase = 2
        # phase = 0 when expecting a question
        # phase = 1 when expecting an answer
        # phase = 2 when neither
        self.answers = []
        self.question = None
        self.answer = []
        self.existing = True
        self.answer_dict = {}
        self.customer = None
        self.pet = None

    def process_answer(self):
        if not self.question:
            return

        self.answers.append((self.question, '\n'.join(self.answer)))
        self.answer_dict[question] = answer

    def handle_starttag(self, tag, attrs):
        if tag != 'tr':
            return
        attr = dict(attrs)

        if 'bgcolor' in attr:
            if attr['bgcolor'] == '#EAF2FA':
                self.process_answer()
                self.phase = 0
                return
            if attr['bgcolor'] == '#FFFFFF':
                self.phase = 1
                return

        self.phase = 2

    def handle_endtag(self, tag):
        if tag == 'html':
            self.process_answer()

        if self.existing:
            pass # find existing customer record
        else:
            self.customer = petadmin.Customer(-1)
            self.customer.notes = 'auto-generated'

            if 'Name' in self.answer_dict:
                self.customer.forename = self.answer_dict['Name'].capitalize()

            if 'Surname' in self.answer_dict:
                self.customer.surname = self.answer_dict['Surname'].capitalize()

            if 'Address' in self.answer_dict:
                address_lines = self.answer_dict['Address'].split('\n')
                self.customer.addr1 = address_lines[0]
                last_line = address_lines[-3]
                last_line_words = last_line.split(' ')
                postcode = last_line_words[-1]
                if len(postcode) < 5:
                    postcode = last_line_words[-2] + ' ' + postcode
                    self.customer.postcode = postcode.upper()

                town = last_line[0:-len(postcode)-1]

                self.customer.addr3 = town
                self.customer.postcode = postcode

            if 'Phone' in self.answer_dict:
                home_phone = self.answer_dict['Phone']
                if home_phone[0:5] == '01236':
                    home_phone = home_phone[5:].strip()

                if home_phone[0:1] == '07':
                    self.customer.telno_mobile = home_phone
                else:
                    self.customer.telno_home = home_phone

            if 'Mobile Phone' in self.answer_dict:
                self.customer.telno_mobile = self.answer_dict['Mobile Phone']

            if 'Email' in self.answer_dict:
                self.customer.email = self.answer_dict['Email']

            if 'Number of pets' in self.answer_dict:
                self.customer.notes = '%d pets' % self.answer_dict['Number of pets']
                if self.answer_dict['Number of pets'] == 1:
                    self.pet = petadmin.Pet(-1)

            if 'Pet Name' in self.answer_dict:
                pet_name = self.answer_dict['Pet Name']
                self.customer.notes += '\nPet Name: %s' % pet_name
                if self.pet:
                    self.pet.name = pet_name

            if 'Category' in self.answer_dict:
                species = self.answer_dict['Category']
                self.customer.notes += '\nPet Spec: %s' % species
                if self.pet:
                    self.pet.spec == species

            if 'Breed' in self.answer_dict:
                breed = self.answer_dict['Breed']
                self.customer.notes += '\nPet Breed: %s' % breed
                if self.pet:
                    self.pet.breed = breed

            if 'Start Date' in self.answer_dict:
                self.customer.notes += '\nStart Date: %s' % self.answer_dict['Start Date']

            if 'End Date' in self.answer_dict:
                self.customer.notes += '\nEnd Date: %s' % self.answer_dict['End Date']


    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.phase == 0:
            self.question = data
            if data == 'How did you hear about us?':
                self.existing = False

            self.answer = []
            return

        if self.phase == 1:
            self.answer.append(data)


# instantiate the parser and fed it some HTML
parser = BookingRequestHTMLParser()

f = open('booking.html')
parser.feed(f.read())

for (question, answer) in parser.answers:
    print 'Question: ', question
    print answer

