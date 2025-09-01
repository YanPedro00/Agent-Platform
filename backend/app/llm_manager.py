from sqlalchemy.orm import Session
from app import models, schemas
from openai import OpenAI
import requests
import json
from typing import Dict, Any

class LLMManager:
    @staticmethod
    def create_llm(db: Session, llm: schemas.LLMCreate):
        # Check for duplicate names
        existing_llm = db.query(models.LLM).filter(models.LLM.name == llm.name).first()
        if existing_llm:
            raise ValueError(f"LLM with name '{llm.name}' already exists")
        
        db_llm = models.LLM(
            name=llm.name,
            provider=llm.provider,
            api_key=llm.api_key,
            base_url=llm.base_url,
            model_name=llm.model_name,
            context_window=llm.context_window,
            max_tokens=llm.max_tokens,
            temperature=llm.temperature
        )
        db.add(db_llm)
        db.commit()
        db.refresh(db_llm)
        return db_llm

    @staticmethod
    def get_llms(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.LLM).offset(skip).limit(limit).all()

    @staticmethod
    def call_llm(llm: models.LLM, prompt: str, conversation_history=None, **kwargs):
        if llm.provider == "openai":
            return LLMManager._call_openai(llm, prompt, conversation_history, **kwargs)
        elif llm.provider == "lmstudio":
            return LLMManager._call_lmstudio(llm, prompt, conversation_history, **kwargs)
        elif llm.provider == "ollama":
            return LLMManager._call_ollama(llm, prompt, conversation_history, **kwargs)
        elif llm.provider == "custom":
            return LLMManager._call_custom_api(llm, prompt, conversation_history, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {llm.provider}")

    @staticmethod
    def _call_openai(llm: models.LLM, prompt: str, conversation_history=None, **kwargs):
        # Correct configuration for the latest OpenAI version
        client_params = {
            "api_key": llm.api_key
        }

        if llm.base_url:
            client_params["base_url"] = llm.base_url

        client = OpenAI(**client_params)

        # Prepare messages
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        else:
            # Add system prompt if no history
            messages.append({"role": "system", "content": "You are a helpful assistant."})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=llm.model_name,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', llm.max_tokens or 1000),
                temperature=kwargs.get('temperature', llm.temperature or 0.1),
                **{k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature']}
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling OpenAI API: {str(e)}"

    @staticmethod
    def _call_lmstudio(llm: models.LLM, prompt: str, conversation_history=None, **kwargs):
        # LM Studio uses OpenAI-compatible API
        client_params = {
            "api_key": llm.api_key or "lm-studio",  # LM Studio usually doesn't require a key
            "base_url": llm.base_url or "http://localhost:1234/v1"  # Default LM Studio URL
        }

        client = OpenAI(**client_params)

        # Prepare messages
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        else:
            # Add system prompt if no history
            messages.append({"role": "system", "content": "You are a helpful assistant."})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=llm.model_name,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', llm.max_tokens or 1000),
                temperature=kwargs.get('temperature', llm.temperature or 0.1),
                **{k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature']}
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling LM Studio API: {str(e)}"

    @staticmethod
    def _call_ollama(llm: models.LLM, prompt: str, conversation_history=None, **kwargs):
        # Ollama tem uma API diferente
        base_url = llm.base_url or "http://localhost:11434"
        endpoint = f"{base_url}/api/generate"

        # Prepare full prompt with conversation history
        full_prompt = ""
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "system":
                    full_prompt += f"System: {msg['content']}\n"
                elif msg["role"] == "user":
                    full_prompt += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    full_prompt += f"Assistant: {msg['content']}\n"
        
        full_prompt += f"User: {prompt}\nAssistant:"

        payload = {
            "model": llm.model_name,
            "prompt": full_prompt,
            "options": {
                "temperature": kwargs.get('temperature', llm.temperature or 0.1),
                "num_predict": kwargs.get('max_tokens', llm.max_tokens or 1000)
            }
        }

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "No response from Ollama")
        except Exception as e:
            return f"Error calling Ollama API: {str(e)}"

    @staticmethod
    def _call_custom_api(llm: models.LLM, prompt: str, conversation_history=None, **kwargs):
        # Implementation for custom API endpoints
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm.api_key}" if llm.api_key else ""
        }

        # Prepare full prompt with conversation history
        full_prompt = ""
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "system":
                    full_prompt += f"System: {msg['content']}\n"
                elif msg["role"] == "user":
                    full_prompt += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    full_prompt += f"Assistant: {msg['content']}\n"
        
        full_prompt += f"User: {prompt}\nAssistant:"

        # Generic payload for custom APIs
        payload = {
            "model": llm.model_name,
            "prompt": full_prompt,
            "max_tokens": kwargs.get('max_tokens', llm.max_tokens or 1000),
            "temperature": kwargs.get('temperature', llm.temperature or 0.1),
            **kwargs
        }

        try:
            response = requests.post(llm.base_url, headers=headers, json=payload)
            response.raise_for_status()

            # Tenta extrair a resposta de diferentes formatos de API
            result = response.json()
            if "text" in result:
                return result["text"]
            elif "response" in result:
                return result["response"]
            elif "choices" in result and len(result["choices"]) > 0:
                if "text" in result["choices"][0]:
                    return result["choices"][0]["text"]
                elif "message" in result["choices"][0]:
                    return result["choices"][0]["message"]["content"]
            else:
                return str(result)
        except Exception as e:
            return f"Error calling custom API: {str(e)}"

    @staticmethod
    def update_llm(db: Session, llm_id: int, llm: schemas.LLMUpdate):
        db_llm = db.query(models.LLM).filter(models.LLM.id == llm_id).first()
        if not db_llm:
            return None

        # Check for duplicate names if name is being updated
        if llm.name and llm.name != db_llm.name:
            existing_llm = db.query(models.LLM).filter(models.LLM.name == llm.name).first()
            if existing_llm:
                raise ValueError(f"LLM with name '{llm.name}' already exists")

        update_data = llm.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_llm, field, value)

        db.commit()
        db.refresh(db_llm)
        return db_llm

    @staticmethod
    def delete_llm(db: Session, llm_id: int):
        db_llm = db.query(models.LLM).filter(models.LLM.id == llm_id).first()
        if not db_llm:
            return False

        db.delete(db_llm)
        db.commit()
        return True