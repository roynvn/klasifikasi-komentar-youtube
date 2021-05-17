import os
import json
import re,itertools
import Levenshtein
from . import csstemmer

class MPStemmer:
    

    def __init__(self, check_nonstandard=True, kosakata=None):
        path = os.path.dirname(__file__)
        default_dict_path = path + '/kbbi_words.txt'
        common_informal_dict_path = path + '/common_informal.json'

        if kosakata == None:
            wordlist = open(default_dict_path, 'r').read().split('\n')
            self.kosakata = {
                kata.lower() for kata in wordlist
            }

            '''
            Catatan kata ambigu:
            -------------------
            kurang -> urang, 
            ukur -> kukur
            
            buang salah satunya atau perhitungkan konteks sekitar kata.
            LoL, buang aja yang ngga sering muncul.
            '''
            self.kosakata.remove('adap')
            self.kosakata.remove('kukur')
            self.kosakata.remove('ketemu')
            self.kosakata.remove('kesohor')
            self.kosakata.remove('soba')
            self.kosakata.remove('urang')
            self.kosakata.remove('urita')
            self.kosakata.remove('gera')
        else:
            self.kosakata = kosakata

        self.common_informal_dict = json.loads(open(common_informal_dict_path, 'r').read())

        self.memo = {}

        self.check_nonstandard = check_nonstandard

    def get_top_n_matching(self, kata, n):
        """
        Mencari n kata yang paling mirip dengan `kata`, diukur berdasarkan string edit distance
        :param kata: kata kunci pencarian
        :param n: jumlah kata termirip yang dicari
        :return: `list` berisi `n` kata yang paling mirip dengan `kata`
        """
        dists = [{'dist': Levenshtein.distance(kata, x), 'word': x} for x in self.kosakata]
        dists_sorted = sorted(dists, key=lambda x: x['dist'])
        return [x['word'] for x in dists_sorted[:n]]

    def get_top_1_matching(self, kata):
        return self.get_top_n_matching(kata, 1)[0]

    def fix_common(self, kata):
        """
        Bakukan kata tak baku yang lazim ditemui, seperti 'ngga' (tidak), 'bgt' (banget), dll.
        :param kata: kata yang akan diperbaiki
        :return: tuple `res` (str) dan `fixed` (bool), masing-masing berisi kata yang dibakukan dan status
        apakah kata berhasil dibakukan (atau ditemui pada daftar kata informal lazim).
        """
        res = kata
        fixed = False
        abb_dict = self.common_informal_dict

        if kata in abb_dict.keys():
            res = abb_dict[kata]
            fixed = True
            return res, fixed

        return res, fixed

    @staticmethod
    def check_nonstandard_affixed(kata):
        """
        Heuristik cepat dan sederhana untuk menentukan baku-tidaknya suatu kata.
        Pastikan sebelumnya kata memang tidak ditemukan di kosakata KBBI (dengan pencarian eksak).
        :param kata:
        :return:
        """
        res = kata
        maybe_nonstandard = False
        if res.startswith(('m', 'n', 'ng', 'ny', 'ke')) or res.endswith(('i', 'in', 'an')):
            maybe_nonstandard = True
        return maybe_nonstandard

    @staticmethod
    def ensure_standard_root(kata, kosakata):
        """
        Kata diasumsikan tidak baku. Harus dilakukan pemeriksaan terlebih dahulu sebelum menggunakan fungsi ini.
        Pastikan suffix telah dibuang terlebih dahulu.
        Fungsi ini melakukan perbaikan minor untuk kata-kata seperti, sebel->sebal, (se|menye|nye)sel->nyesal.
        :param kata:
        :param kosakata:
        :return:
        """
        res = kata
        if not (res[-1] in 'aiueo') and (res[-2] == 'e'):
            case1 = res
            case2 = case1[:-2] + 'a' + case1[-1:]

            if case1 in kosakata:
                res = case1
            elif case2 in kosakata:
                res = case2
        return res

    def standardify(self, kata):
        res = kata
        if (res[-1] in ['p']) and (res[-2] == 'e'):
            res = res[:-2] + 'a' + res[-1:]
        return res

    @staticmethod
    def fix_nonstandard_prefix(kata):
        """
        Kata diasumsikan tidak baku. Harus dilakukan pemeriksaan terlebih dahulu sebelum menggunakan fungsi ini.
        Fungsi ini tidak benar-benar memperbaiki suffix hingga memperoleh bentuk valid, a.l., ngeberesin --> mengeberes.
        Stemming lanjutan akan ditangani oleh stemmer standar, a.l., confix-stripping, dll.
        :param kata:
        :return:
        """
        res = kata
        if res.startswith(('m', 'n', 'ng', 'ny')):
            if res.startswith('nge') and not (res[3] in ['m', 'n']):
                res = res[3:]
            else:
                res = 'me' + res

        elif res.startswith('ke'):
            res = res[2:]

        elif res.startswith(('gini', 'gitu')):
            res = 'be' + res

        return res

    @staticmethod
    def fix_nonstandard_suffix(kata):
        res = kata
        # buang suffix sederhana
        if res.endswith('in'):
            res = res[:-2]
            # elif res.endswith('i'):
        #     res = res[:-1]
        return res


    def stem(self, kata, prioritize_standard=True, rigor=False):
        res = kata
        res = res.lower()
        #menghapus kata-kata ganda seperti makan-makan jadi makan
        res = re.sub(r"\b(\w+)(?:\W\1\b)+", r"\1", res, flags=re.IGNORECASE)
        #remove tab, new line, ans back slice
        res = res.replace("\\t"," ").replace("\\n"," ").replace("\\u"," ").replace("\\","")
        #remove number
        res = re.sub(r"\d+", "", res)
        #remove punctuation/tanda baca
        res=  re.sub(r'[\W\s]', ' ', res)
        #remove whitespace leading & trailing/ spasi
        res = res.strip()
        #remove multiple whitespace into single whitespace
        res = re.sub("\s+"," ",res)
       
    
        """
        :param kata: kata yang ingin dicari akarnya
        :param kosakata: Daftar kata dasar
        :param prioritize_standard: Berguna untuk artikel dengan mayoritas kata baku, seperti teks berita, tulisan ilmiah, dll.
        :param rigor: Jika hasil akhir tidak dapat ditemukan di kosakata, cari kata terdekat lebih detail
        :return: akar kata
        """
        

        """
        Coba perbaiki kata nonstandar yang biasa ditemui. Biasanya berupa singkatan/saltik.
        """
        res, fixed = self.fix_common(res)
        if fixed:
            return res

        """
        Jangan stem jika kata pendek.
        """
        if len(res) <= 3:
            return res

        """
        Jika kata sudah pernah di-stem sebelumnya, maka gunakan hasil yang sudah ada.
        """
        if res in self.memo:
            return self.memo[res]

        """ 
        Lapis 1: cari di KBBI (eksak). 
        """
        if res in self.kosakata:
            return res

        """
        Lapis 2: jalankan stemmer biasa, jika pengecekan kata baku diprioritaskan. 
        """
        if prioritize_standard:
            res = csstemmer.stem(res, self.kosakata)
            if res in self.kosakata:
                self.memo[kata] = res
                return res
            else:
                res = kata

        """ 
        Lapis 3: cek kemungkinan kata tak baku terafiksasi. Jika ya, bakukan afiksasi.
        """
        if self.check_nonstandard:
            maybe_nonstandard = self.check_nonstandard_affixed(res)
            if maybe_nonstandard:

                res = self.fix_nonstandard_suffix(res)
                if res in self.kosakata:
                    self.memo[kata] = res
                    return res

                res = self.fix_nonstandard_prefix(res)
                if res in self.kosakata:
                    self.memo[kata] = res
                    return res

            """ 
            Lapis 4: Setelah lapis 3, ada kemungkinan kata masih terafiksasi. Lakukan stemming standar,
            karena afiksasi telah dibakukan di lapis 3. 
            """
            res = self.standardify(res)
            res = csstemmer.stem(res, self.kosakata)

            """ 
            Lapis 5: Hasil lapis 4 belum tentu memperoleh akar kata baku. Karena itu, jika sebelumnya kata telah
            terindikasi tidak baku, pastikan akar kata dibakukan. 
            """
            res = self.ensure_standard_root(res, self.kosakata)

            """ 
            Lapis 6: Opsional. Pencarian lebih detail melalui similarity search, jika hasil dari lapis 5 tak ditemukan 
            di kosakata. 
            PERINGATAN!!! Ini bisa memakan banyak waktu. 
            """
            if rigor and maybe_nonstandard:
                res = self.get_top_1_matching(res)

        self.memo[kata] = res
        # print('final res: ', res)
        if res in self.kosakata:
            return res
        else:
            return kata

    def stem_kalimat(self, kalimat, prioritize_standard=True, rigor=False):
        """
        :param kalimat: Kalimat (baris kata terpisah spasi) yang akan dibakukan.
        Sementara ini, karakter non-alfanumerik akan dihilangkan.
        :return: Kalimat berisi kata-kata yang sudah dibakukan.
        """
        res = []
        words = kalimat.lower().split(' ')


        for kata in words:
            root = self.stem(kata, prioritize_standard, rigor)
            res.append(root)
        return ' '.join(res)


if __name__ == '__main__':
   
    kata_uji = [
        
        'doakan','memakannya','menjadikan','memakan','beranak','beragam','memastikan','memerlukan','kuah','menyontek','nyamar','nyontek','nyapu','nyomot','berjalan','nyobain','nyoba','Makanan','bersihk3an','cobain','bersalin','mamer','dikepalanya','dikumpulkan','dibandingkan','nyaman','kebanyakan','keperluan','disukai','banyakan','pekerjakan','memperbaiki','mempunyai','memperlakukan','mempekerjakannya','kuat','menjadikan','inginkan','pingin','memakan','memrakarsa','memamerkan','melihat','mengadukan','mengajarkan','mengatakan','mengeluarkan','menjadi','penyakit','bercerita','bersihkan','melarikan','berlarian','ternak','termakan','kebanyakan','keenakan','enakan','bermain','kunjungi','kuminum','kumakan','dimananya','dimanakah','dimanalah','makan-makan','dimakannya','disini','dilihatnya','disana','ditanya','makanya','termakan','dimakan','disana','penyakit','belajar','kumakan','nyebrang','nilaiku', 'berai', 'bukankah', 'bercerita', 'berlarian', 'belajar', 'beterbangan',  
        'terangkat', 'terundung',   # te-
        'mempunyai', 'memamerkan', 'memrakarsai', 'menengok', 'menasal', 'mengasihaninya', 
    ]

    stemmer = MPStemmer()

    for kata in kata_uji:
        print(f'{kata} -> {stemmer.stem(kata)}')
