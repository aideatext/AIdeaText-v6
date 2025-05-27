from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset
import json
import tqdm

tokenizer = GPT2Tokenizer.from_pretrained("openai-community/gpt2")
model = GPT2LMHeadModel.from_pretrained("openai-community/gpt2")

class MultilingualChatData(Dataset):
    def __init__(self, file_path, tokenizer, max_length=512):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        input_text = f"<startofstring> {item['input']} <bot>: {item['output']} <endofstring>"
        encoding = self.tokenizer(input_text, truncation=True, padding='max_length', max_length=self.max_length, return_tensors="pt")
        return encoding['input_ids'].squeeze(), encoding['attention_mask'].squeeze()

class MultilingualChatbot:
    def __init__(self):
        self.models = {
            'en': GPT2LMHeadModel.from_pretrained("microsoft/DialoGPT-medium"),
            'es': GPT2LMHeadModel.from_pretrained("DeepESP/gpt2-spanish"),
            'fr': GPT2LMHeadModel.from_pretrained("asi/gpt-fr-cased-small")
        }
        self.tokenizers = {
            'en': GPT2Tokenizer.from_pretrained("microsoft/DialoGPT-medium"),
            'es': GPT2Tokenizer.from_pretrained("DeepESP/gpt2-spanish"),
            'fr': GPT2Tokenizer.from_pretrained("asi/gpt-fr-cased-small")
        }
        for tokenizer in self.tokenizers.values():
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.add_special_tokens({
                "bos_token": "<startofstring>",
                "eos_token": "<endofstring>"
            })
            tokenizer.add_tokens(["<bot>:"])
        
        for model in self.models.values():
            model.resize_token_embeddings(len(self.tokenizers['en']))  # Assuming all tokenizers have the same vocabulary size
        
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        for model in self.models.values():
            model.to(self.device)

    def train(self, lang, data_file, epochs=5, batch_size=32, learning_rate=1e-4):
        model = self.models[lang]
        tokenizer = self.tokenizers[lang]
        
        chat_data = MultilingualChatData(data_file, tokenizer)
        data_loader = DataLoader(chat_data, batch_size=batch_size, shuffle=True)
        
        optimizer = Adam(model.parameters(), lr=learning_rate)
        
        model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch in tqdm.tqdm(data_loader, desc=f"Epoch {epoch+1}/{epochs}"):
                input_ids, attention_mask = [b.to(self.device) for b in batch]
                
                optimizer.zero_grad()
                outputs = model(input_ids, attention_mask=attention_mask, labels=input_ids)
                loss = outputs.loss
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(data_loader):.4f}")
        
        torch.save(model.state_dict(), f"model_state_{lang}.pt")

    def generate_response(self, prompt, src_lang):
        model = self.models.get(src_lang, self.models['en'])
        tokenizer = self.tokenizers.get(src_lang, self.tokenizers['en'])
        
        input_text = f"<startofstring> {prompt} <bot>: "
        input_ids = tokenizer.encode(input_text, return_tensors='pt').to(self.device)
        
        attention_mask = torch.ones(input_ids.shape, dtype=torch.long, device=self.device)
        
        output = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=1000,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            num_return_sequences=1,
            length_penalty=1.0,
            repetition_penalty=1.2
        )
        
        decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
        return decoded_output.split("<bot>:")[-1].strip()

def initialize_chatbot():
    return MultilingualChatbot()

def get_chatbot_response(chatbot, prompt, src_lang):
    return chatbot.generate_response(prompt, src_lang)

# Ejemplo de uso
if __name__ == "__main__":
    chatbot = initialize_chatbot()
    
    # Entrenar el modelo en español (asumiendo que tienes un archivo de datos en español)
    chatbot.train('es', './spanish_chat_data.json', epochs=3)
    
    # Generar respuestas
    print(get_chatbot_response(chatbot, "Hola, ¿cómo estás?", 'es'))
    print(get_chatbot_response(chatbot, "Hello, how are you?", 'en'))
    print(get_chatbot_response(chatbot, "Bonjour, comment allez-vous?", 'fr'))