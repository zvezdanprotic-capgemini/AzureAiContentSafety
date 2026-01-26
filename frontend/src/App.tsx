import { ChakraProvider } from '@chakra-ui/react';
import { ChatContainer } from './components/ChatContainer';

function App() {
  return (
    <ChakraProvider>
      <ChatContainer />
    </ChakraProvider>
  )
}

export default App
