from dataclasses import dataclass


@dataclass
class Config:
    num_layers: int
    d_model: int
    num_heads: int
    d_ff: int
    vocab_size: int
    max_position_encoding: int


@dataclass
class TransformerConfig:
    num_layers: int = 6
    d_model: int = 512
    num_heads: int = 8
    d_ff: int = 2048
    vocab_size: int = 32000
    max_position_encoding: int = 512
