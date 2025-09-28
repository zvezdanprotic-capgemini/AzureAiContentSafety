import { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  Input,
  IconButton,
  Flex,
  useToast,
} from '@chakra-ui/react';
import { ChatMessage } from './ChatMessage';
import type { Message } from '../types';
import axios from 'axios';
import { ArrowUpIcon } from '@chakra-ui/icons';

export const ChatContainer = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: userMessage.content,
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.response,
        role: 'bot',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to get response from the bot.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box h="100vh" p={4}>
      <VStack h="full" spacing={4}>
        <Box
          flex={1}
          w="full"
          overflowY="auto"
          borderWidth={1}
          borderRadius="lg"
          p={4}
        >
          <VStack align="stretch" spacing={4}>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </VStack>
        </Box>
        <Flex w="full">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSubmit();
              }
            }}
            mr={2}
          />
          <IconButton
            colorScheme="blue"
            aria-label="Send message"
            icon={<ArrowUpIcon />}
            onClick={handleSubmit}
            isLoading={isLoading}
          />
        </Flex>
      </VStack>
    </Box>
  );
};