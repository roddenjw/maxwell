"""
Local LLM Service using llama-cpp-python

Provides offline AI capabilities for Maxwell through local GGUF models.
Supports automatic GPU detection and capability assessment.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration


# Default models directory
MODELS_DIR = Path(os.getenv("MODELS_DIR", "./models"))


class ModelCapability(str, Enum):
    """Model capability tiers based on size/performance"""
    MINIMAL = "minimal"      # < 4B parameters - basic completions
    STANDARD = "standard"    # 4-13B parameters - good reasoning
    ADVANCED = "advanced"    # > 13B parameters - best quality


@dataclass
class LocalModelInfo:
    """Information about a local model"""
    name: str
    path: str
    size_bytes: int
    capability: ModelCapability
    context_length: int
    quantization: str  # Q4_K_M, Q5_K_M, etc.

    @property
    def size_gb(self) -> float:
        return round(self.size_bytes / (1024**3), 2)


def detect_model_capability(path: str, size_bytes: int) -> ModelCapability:
    """
    Detect model capability based on filename and size

    Common patterns:
    - 7B models: ~4-8GB quantized
    - 13B models: ~7-13GB quantized
    - 70B models: ~35-70GB quantized
    """
    filename = os.path.basename(path).lower()
    size_gb = size_bytes / (1024**3)

    # Check filename hints
    if "70b" in filename or "72b" in filename:
        return ModelCapability.ADVANCED
    if "34b" in filename or "33b" in filename:
        return ModelCapability.ADVANCED
    if "13b" in filename:
        return ModelCapability.STANDARD
    if "7b" in filename or "8b" in filename:
        return ModelCapability.STANDARD
    if "3b" in filename or "2b" in filename or "1b" in filename:
        return ModelCapability.MINIMAL

    # Fallback to size-based detection
    if size_gb > 25:
        return ModelCapability.ADVANCED
    elif size_gb > 6:
        return ModelCapability.STANDARD
    else:
        return ModelCapability.MINIMAL


def detect_quantization(filename: str) -> str:
    """Extract quantization type from filename"""
    filename = filename.upper()
    quant_types = [
        "Q8_0", "Q6_K", "Q5_K_M", "Q5_K_S", "Q5_0",
        "Q4_K_M", "Q4_K_S", "Q4_0", "Q3_K_M", "Q3_K_S",
        "Q2_K", "IQ4_XS", "IQ3_XXS", "F16", "F32"
    ]
    for qt in quant_types:
        if qt in filename:
            return qt
    return "unknown"


def detect_context_length(filename: str) -> int:
    """Estimate context length from filename hints"""
    filename = filename.lower()
    if "128k" in filename:
        return 131072
    if "32k" in filename:
        return 32768
    if "16k" in filename:
        return 16384
    if "8k" in filename:
        return 8192
    # Default
    return 4096


class LocalLLM(BaseChatModel):
    """LangChain-compatible wrapper for llama-cpp-python"""

    model_path: str
    n_ctx: int = 4096
    n_gpu_layers: int = -1  # -1 for auto
    temperature: float = 0.7
    max_tokens: int = 2048
    _llm: Any = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_model()

    def _load_model(self):
        """Load the llama-cpp model"""
        try:
            from llama_cpp import Llama

            # Determine GPU layers
            n_gpu = self.n_gpu_layers
            if n_gpu == -1:
                # Auto-detect GPU
                try:
                    import torch
                    if torch.cuda.is_available():
                        n_gpu = 999  # Offload all layers to GPU
                    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        n_gpu = 999  # Apple Metal
                    else:
                        n_gpu = 0
                except ImportError:
                    n_gpu = 0  # CPU only

            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=n_gpu,
                verbose=False
            )
        except ImportError:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Install it with: pip install llama-cpp-python"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    @property
    def _llm_type(self) -> str:
        return "local-llama"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> ChatResult:
        """Generate response from messages"""
        # Format messages for llama
        prompt = self._format_messages(messages)

        # Generate
        response = self._llm(
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop=stop,
            echo=False
        )

        # Extract text
        text = response["choices"][0]["text"].strip()

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=text),
                    generation_info={
                        "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                        "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
                    }
                )
            ]
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> ChatResult:
        """Async generate - wraps sync for now"""
        import asyncio
        return await asyncio.to_thread(
            self._generate, messages, stop, **kwargs
        )

    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """Format messages into a prompt string"""
        # Use ChatML format
        prompt_parts = []

        for msg in messages:
            if msg.type == "system":
                prompt_parts.append(f"<|im_start|>system\n{msg.content}<|im_end|>")
            elif msg.type == "human":
                prompt_parts.append(f"<|im_start|>user\n{msg.content}<|im_end|>")
            elif msg.type == "ai":
                prompt_parts.append(f"<|im_start|>assistant\n{msg.content}<|im_end|>")

        prompt_parts.append("<|im_start|>assistant\n")
        return "\n".join(prompt_parts)


class LocalLLMService:
    """
    Service for managing local LLM models

    Features:
    - Model discovery from models/ directory
    - Capability detection
    - GPU acceleration support
    - Memory management
    """

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or MODELS_DIR
        self._current_model: Optional[LocalLLM] = None
        self._current_model_path: Optional[str] = None

    def is_available(self) -> bool:
        """Check if local LLM support is available"""
        try:
            from llama_cpp import Llama
            return True
        except ImportError:
            return False

    def list_models(self) -> List[LocalModelInfo]:
        """
        List available local models

        Returns:
            List of LocalModelInfo for each discovered model
        """
        models = []

        if not self.models_dir.exists():
            return models

        # Find GGUF files
        for path in self.models_dir.glob("**/*.gguf"):
            try:
                stat = path.stat()
                models.append(LocalModelInfo(
                    name=path.stem,
                    path=str(path),
                    size_bytes=stat.st_size,
                    capability=detect_model_capability(str(path), stat.st_size),
                    context_length=detect_context_length(path.name),
                    quantization=detect_quantization(path.name)
                ))
            except Exception:
                continue

        # Sort by capability (advanced first)
        capability_order = {
            ModelCapability.ADVANCED: 0,
            ModelCapability.STANDARD: 1,
            ModelCapability.MINIMAL: 2
        }
        models.sort(key=lambda m: capability_order[m.capability])

        return models

    def get_model_info(self, model_path: str) -> Optional[LocalModelInfo]:
        """Get info for a specific model"""
        path = Path(model_path)
        if not path.exists():
            return None

        stat = path.stat()
        return LocalModelInfo(
            name=path.stem,
            path=str(path),
            size_bytes=stat.st_size,
            capability=detect_model_capability(str(path), stat.st_size),
            context_length=detect_context_length(path.name),
            quantization=detect_quantization(path.name)
        )

    def get_langchain_model(self, config) -> LocalLLM:
        """
        Get or create a LangChain-compatible local model

        Reuses loaded model if same path to avoid reloading.
        """
        model_path = config.model_path

        if not model_path:
            # Try to find a model
            models = self.list_models()
            if not models:
                raise ValueError(
                    "No local models found. Place GGUF files in the models/ directory."
                )
            model_path = models[0].path

        # Check if we can reuse current model
        if self._current_model and self._current_model_path == model_path:
            return self._current_model

        # Load new model
        self._current_model = LocalLLM(
            model_path=model_path,
            n_ctx=config.n_ctx,
            n_gpu_layers=config.n_gpu_layers,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        self._current_model_path = model_path

        return self._current_model

    def unload_model(self):
        """Unload current model to free memory"""
        if self._current_model:
            del self._current_model._llm
            self._current_model = None
            self._current_model_path = None

            # Force garbage collection
            import gc
            gc.collect()

    def get_recommended_model(self) -> Optional[LocalModelInfo]:
        """
        Get the recommended model based on system capabilities

        Prioritizes:
        1. Standard capability (good balance)
        2. Models with > 4096 context
        3. Better quantization (Q5 > Q4 > Q3)
        """
        models = self.list_models()
        if not models:
            return None

        # Filter for standard capability
        standard_models = [m for m in models if m.capability == ModelCapability.STANDARD]
        if not standard_models:
            standard_models = models

        # Prefer larger context
        standard_models.sort(key=lambda m: m.context_length, reverse=True)

        # Among equal context, prefer better quantization
        quant_order = {"Q8_0": 0, "Q6_K": 1, "Q5_K_M": 2, "Q5_K_S": 3,
                       "Q4_K_M": 4, "Q4_K_S": 5, "unknown": 6}
        standard_models.sort(
            key=lambda m: quant_order.get(m.quantization, 5)
        )

        return standard_models[0]


# Global instance
local_llm_service = LocalLLMService()
