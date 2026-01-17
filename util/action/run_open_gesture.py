from util.ip_helper import IPHelper
from util.action.conversational_gesture import ConversationGesture
from unitree_sdk2py.core.channel import ChannelFactoryInitialize

def main():
    network_interface = IPHelper.get_network_interface('192.168.123.*')
    ChannelFactoryInitialize(0, network_interface)

    custom_action = ConversationGesture()
    custom_action.open_gesture()

if __name__ == '__main__':
    main()