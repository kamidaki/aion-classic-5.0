//! Constantes do handshake STS, copiadas da captura do servidor oficial.
//!
//! `ServerPublicKey` e `ServerSignature` chegam **byte a byte identicos** nas capturas de 21/08 e
//! 23/08 de 2026 -- sessoes diferentes, dias diferentes. Sao constantes do servico, nao material
//! de sessao: a assinatura nao cobre o `ServerRand`, que e o unico campo que muda.

/// Chave publica RSA do servico, em base64. Decodificada sao 268 bytes:
/// `u32 tipo=4 | u32 expoente=65537 | u32 tamanho=256 | modulo[256]`.
pub const SERVER_PUBLIC_KEY: &str = concat!(
    "BAAAAAEAAQAAAQAA59gFMrcvhedHWl48CvoLFg2y30kxxqHuqwHZw8NVWQcyxzINUZABPKGii9d75BhEJKtS517J",
    "E8xvUgsEtVbtyt6sEYrXtkkl/XDPc+bbkf/klEi3vU0Q2u9Ju3BRSB8nlVJmR3O/3kX+oFolv3hnJ6257Kaj9KGu",
    "RRurwJpV9PXAJGA2M8z6fNfk7fkpOSmuMPuzKU4fjTEZmpDg7IYMNjvE6Ye79R7GeKsDPUoH/f1300FrlrKGatAo",
    "De7XRry9HTWbQmmkLtijSZqu+QlC+maEfLxp7eEOohdcWXbH7EmWklhDAau8Q6MJY177gyTMfh5hyiK2rOPqoNV1",
    "a6UQqQ==",
);

/// Assinatura que acompanha a chave publica. 256 bytes em base64.
pub const SERVER_SIGNATURE: &str = concat!(
    "kh0wnbfWfDV0+aZRHL2l5+OkIjAvmYO3Gi2iw0CBeB4TCBkmxC3yn8ahnZKYjtCaDOho7xVtzU5F7Xxbi69OyLsa",
    "F0KCytBgcfPuLftV1O0anFAt+NWt3ON+SzHLxgqU0kJKBcDhhSpFzYI3mxvYQky1Vi+oaEbBu5e77uB0kefPA0VF",
    "WSC+yBF6seYVAk62utO9ETxBAnhldsZK/NFXc6aSEqbtCYnr5D8Na57zv4O7MJ7NksUUEsOF0XavjeQhwMviYqd+",
    "hnnOr6hZFMVr1sxZ3YG7xSK7uTaF/ZK2Jdn7BNQY+7ihmoTzDUkLcre788TJ//DhsoLObIYaLhPEsA==",
);
