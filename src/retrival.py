import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def retrival(query_emb, gallery_embs, top_k=3):
    """
    Retrieve the top_k most similar gallery embeddings to the query embedding.
    
    Args:
        query_emb (np.ndarray): The embedding of the query image.
        gallery_embs (np.ndarray): The embeddings of the gallery images.
        top_k (int): The number of top similar images to retrieve.
        
    Returns:
        np.ndarray: Indices of the top_k most similar gallery embeddings.
    """
    # Compute cosine similarity between query and gallery embeddings
    sims = cosine_similarity(query_emb, gallery_embs)
    
    # Get indices of the top_k most similar embeddings
    idxs = np.argsort(sims[0])[top_k:]
    return idxs, sims[0,idxs]