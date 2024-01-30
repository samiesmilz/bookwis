import speech_recognition as sr
import pyttsx3

# initialize the recognizer
r = sr.Recognizer()


def record_text():
    # Loop incase of errors
    while (1):
        try:
            # use the computer microphone as the source of input
            with sr.Microphone() as source2:

                # listen for the user's input
                r.adjust_for_ambient_noise(source2, duration=0.2)

                # listen for the user's input
                audio2 = r.listen(source2)

                # Using google to recognise the audio
                MyText = r.recognize_google(audio2)

                return MyText

        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))

        except sr.UnknownValueError:
            print("unknown error occured.")

    return


def output_text(text):
    f = open("output.txt", "a")
    f.write(text)
    f.write("\n")
    f.close()

    return


while (1):
    text = record_text()
    output_text(text)

    print("Wrote text")
