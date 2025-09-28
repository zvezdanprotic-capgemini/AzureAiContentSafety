import { Box, Text } from '@chakra-ui/react';
import type { Message } from '../types';

type ChatMessageProps = {
  message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  return (
    <Box
      maxW="80%"
      mb={4}
      alignSelf={message.role === 'user' ? 'flex-end' : 'flex-start'}
      bg={message.role === 'user' ? 'blue.500' : 'gray.200'}
      color={message.role === 'user' ? 'white' : 'black'}
      p={4}
      borderRadius="lg"
    >
      <Text>{message.content}</Text>
      <Text fontSize="xs" color={message.role === 'user' ? 'whiteAlpha.700' : 'gray.500'} mt={1}>
        {new Date(message.timestamp).toLocaleTimeString()}
      </Text>
    </Box>
  );
};