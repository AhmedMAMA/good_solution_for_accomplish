#include "../../libs/TreatFileVideo.h"

FILE* openVideo(const char* filepath){
    FILE* video = fopen(filepath,"rb");
    if(!video)
        printf("Ouverture de la source vidéo refusée.\n");
    else
        return video;
}

bool closeVideo(FILE* filepointer){
    if(!fclose(filepointer))
        return true;
    else
        return false;
}

int main(){
    char* videopath = "/home/ahmed/Bureau/projet_propre/test/video_small.mp4";
    FILE* source  = openVideo(videopath);
    if (source == NULL)
        printf("Ouverture vidéo non effectué.....\n");
    else
        printf("Ouverture effectuée avec succès\n");

    if (closeVideo(source))
        printf("Fermeture source ok.\n");
    else
        printf("Fermeture source non réussi.\n");
}