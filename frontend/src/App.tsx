import { ChakraProvider, Container } from '@chakra-ui/react';
import { ChatContainer } from './components/ChatContainer';

function App() {
  return (
    <ChakraProvider>
      <Container maxW="container.md" py={8}>
        <ChatContainer />
      </Container>
    </ChakraProvider>
  )
}

export default App
