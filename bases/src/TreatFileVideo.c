/**
 * @file TreatFileVideo.c
 * @author Ahmed MAMA (dembenin@gmail.com)
 * @brief  Fichier de description de nos fonctions de traitement vidéo en C.
 * @version 0.1
 * @date 2026-06-04
 * 
 * @copyright Copyright (c) 2026
 * 
 */

#include "../libs/TreatFileVideo.h"

FILE* openVideo(const char* filepath){
    FILE* video = fopen(filepath,"rb");
    if(!video){
        printf("Ouverture de la source vidéo refusée.\n");
        return NULL;
    }
    return video;
}

bool closeVideo(FILE* filepointer){
    if(!fclose(filepointer))
        return true;
    else
        return false;
}