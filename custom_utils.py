def yolo_to_x0y0(yolo_pred, input_w, input_h, target_w, target_h):

    # yolo_x = (x+(w/2))/img_w
    # x_c = (yolo_x) * img_w - (w/2)

    # yolo_width = w/img_w
    # w = yolo_width * img_w

    # target_size / input_size
    x_scale = target_w / input_w
    y_scale = target_h / input_h

    # convert from yolo [x_c, y_c, w_norm, h_norm] to [x0,y0,x1,y1]
    bbox_w = yolo_pred[2] * input_w
    bbox_h = yolo_pred[3] * input_h
    x0_orig = yolo_pred[0] * input_w - (bbox_w/2)
    y0_orig = yolo_pred[1] * input_h - (bbox_h/2)

    x1_orig = x0_orig + bbox_w
    y1_orig = y0_orig + bbox_h

    # scale accoring to target_size
    x = int(x0_orig * x_scale)
    y = int(y0_orig * y_scale)
    xmax = int(x1_orig * x_scale)
    ymax = int(y1_orig * y_scale)

    return [x, y, xmax, ymax]

def voc_to_yolo(size, box):
    dw = 1./(size[0])
    dh = 1./(size[1])
    x = (box[0] + box[2])/2.0 - 1
    y = (box[1] + box[3])/2.0 - 1
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)