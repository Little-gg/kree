#!/usr/bin/env python
# encoding: utf-8


class dict2obj(dict):
    def __init__(self, d, default=None):
        self.__d = d
        self.__default = default
        super(self.__class__, self).__init__(d)

    def __getattr__(self, k):
        if k in self.__d:
            v = self.__d[k]
            if isinstance(v, dict):
                v = self.__class__(v)
            setattr(self, k, v)
            return v
        return self.__default


#  class dict2obj(object):
    #  def __init__(self, dic):
        #  for k, v in dic.items():
            #  # if isinstance(v, (tuple, list)):
            #  #     setattr(self, k, [dict2obj(i) if isinstance(i, dict) else i for i in v])
            #  # else:
            #  #     setattr(self, k, dict2obj(v) if isinstance(v, dict) else v)

            #  if isinstance(v, (tuple, list)):
                #  self.__setattr__(k, [dict2obj(i) if isinstance(i, dict) else i for i in v])
            #  else:
                #  self.__setattr__(k, dict2obj(v) if isinstance(v, dict) else v)
