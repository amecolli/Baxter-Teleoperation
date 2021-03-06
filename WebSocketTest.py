import Leap
from SampleGiada import SampleListener
from tornado.ioloop import PeriodicCallback, IOLoop
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.websocket import WebSocketHandler
import random
import queue

#The current version has been updated to facilitate communication between
#Leap Motion and ROS

class LeapWSHandler(WebSocketHandler):
        clients = [] #list of listening clients
        listener = SampleListener()
        controller = Leap.Controller()
        Q = queue.Queue() #not really used now; for use in case of missed frame

        def check_origin(self, origin):
                return True

        def getLeapData(self):
                # Keep this process running until Enter is pressed
                frame = LeapWSHandler.controller.frame()
                hands = frame.hands
                s = ""

                for hand in frame.hands:
                        handType = "Left hand" if hand.is_left else "Right hand"

                        pos = hand.palm_position
                        #coordinate system convertion: (corrected)
                        #i. leap (x+, y+, z+) -> ROS (y-, z, x-)
                        s += ("%s^%d^%s^" % (
                               handType, hand.id, str((str(-pos.z), str(-pos.x), str(pos.y)))))
                        # Get the hand's normal vector and direction
                        normal    = hand.palm_normal
                        direction = hand.direction

                        pitch = direction.pitch
                        roll = normal.roll
                        yaw = direction.yaw

                        # Calculate the hand's pitch, roll, and yaw angles
                        s += ("%f^%f^%f^" % (
                                pitch,
                                roll,
                                yaw))

                        pinch = hand.pinch_strength
                        s += ("%f^\n" % pinch)
                        
                return self.send_data(s)

        def open(self):
                # Have the sample listener receive events from the controller
                LeapWSHandler.controller.add_listener(LeapWSHandler.listener)
                LeapWSHandler.clients.append(self)
                self.callback = PeriodicCallback(self.getLeapData, 50) #??fps
                self.callback.start()

        def on_message(self, message):
                print("Client message received: " + message)

        def on_close(self):
                # Remove the sample listener when done
                LeapWSHandler.controller.remove_listener(LeapWSHandler.listener)

                LeapWSHandler.clients.remove(self)
                self.callback.stop()

        @classmethod
        def send_data(l, data):
                for client in l.clients:
                        try:
                                client.write_message(data)
                        except:
                                print("Fail to send data to client.")

def main():
        #tornado.ioloop.IOLoop.instance().stop()
        app = Application([
                (r"/ws", LeapWSHandler),
        ])

        hs = HTTPServer(app)
        hs.listen(8888, "128.237.136.61")
        IOLoop.instance().start()

main()
