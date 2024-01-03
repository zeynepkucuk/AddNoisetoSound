# Add Noise to Sound

advanced noise injection
 
 * sound_path dizini altında verilen kişilerin sesleri ile noise_path dizini altında verilen noise'lar mix'lenir.
 
 * Mix'lenmiş sesler save_path alanında verilen dizine kaydedilir. Mixleme işlemi yapılırken her bir wav dosyasının
  percentage kadar uzunluğuna noise eklenir.
    
  * sound_path dizini altında klasörler bulunur, bu klasörler speaker adına karşılık gelir. Bu speaker dizini
    altında da wav veya mp3 dosyaları bulunur.
    noise_path dizini altında ise klasörler bulunmaz. Sadece ilgili noise wav veya mp3 dosyaları bulunur.
    
   * param sound_path: seslerin olduğu dizin
   * param noise_path: noise'ların oldugu dizin
   * param save_path:  yeni seslerin kaydedileceği dizin
   * percentage: seslerin yuzde kacına noise eklenecegi bilgisi girilir
    
    