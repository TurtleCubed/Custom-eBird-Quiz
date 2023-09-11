import requests

def get_photos(birdid='bkcchi'):
    """Test function given by Max"""
    url = f'https://media.ebird.org/api/v2/search?taxonCode={birdid}&sort=rating_rank_desc&mediaType=photo&birdOnly=true'
    out = requests.get(url, cookies={'ml-search-session': 'eyJ1c2VyIjp7ImFub255bW91cyI6dHJ1ZX19', 'ml-search-session.sig': 'XZPO3pJ50PRL94J3OagC3Bg1IVk'})
    out = [x['assetId'] for x in out.json()]
    imgurls = [f'https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{i}/' for i in out]
    return imgurls


if __name__ == "__main__":
    l = get_photos()
    print(l)
    print(len(l))
